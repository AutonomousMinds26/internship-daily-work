from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.database import get_db
from app.models import Interview, Candidate, Job, CandidateHistory
from app.schemas import InterviewCreate, InterviewUpdate, InterviewResponse
from app.auth import RoleChecker, User
from app.services.redis_cache import invalidate_candidate, cache_candidate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["interviews"])

recruiter_manager_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])

def log_candidate_history(db: Session, candidate_id: int, action: str, details: str = None, performed_by: str = None):
    try:
        history = CandidateHistory(
            candidate_id=candidate_id,
            action=action,
            details=details,
            performed_by=performed_by
        )
        db.add(history)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log history for candidate {candidate_id}: {str(e)}")

@router.post("/interview", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
@router.post("/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def schedule_interview(
    interview_in: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_manager_checker)
):
    """
    Schedule a new interview for a candidate and job.
    Updates candidate status to 'Interview Scheduled' and records history.
    """
    logger.info(f"Scheduling interview for candidate {interview_in.candidate_id} and job {interview_in.job_id}")

    candidate = db.query(Candidate).filter(Candidate.id == interview_in.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {interview_in.candidate_id} not found."
        )

    job = db.query(Job).filter(Job.id == interview_in.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {interview_in.job_id} not found."
        )

    db_interview = Interview(
        candidate_id=interview_in.candidate_id,
        job_id=interview_in.job_id,
        interviewer_name=interview_in.interviewer_name,
        interviewer_email=interview_in.interviewer_email,
        scheduled_time=interview_in.scheduled_time,
        duration_minutes=interview_in.duration_minutes or 45,
        mode=interview_in.mode or "Online",
        meeting_link=interview_in.meeting_link,
        notes=interview_in.notes,
        status="Scheduled"
    )
    db.add(db_interview)

    # Update candidate status
    candidate.status = "Interview Scheduled"
    db.commit()
    db.refresh(db_interview)
    db.refresh(candidate)

    invalidate_candidate(candidate.id)
    log_candidate_history(
        db, 
        candidate.id, 
        "Interview Scheduled", 
        f"Scheduled interview with {interview_in.interviewer_name} at {interview_in.scheduled_time}", 
        current_user.username
    )

    logger.info(f"Interview scheduled successfully with ID {db_interview.id}")
    return db_interview


@router.get("/interview", response_model=List[InterviewResponse])
@router.get("/interviews", response_model=List[InterviewResponse])
def get_interviews(
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_auth_checker)
):
    """
    Retrieve scheduled interviews. Supports optional filtering by candidate_id and job_id.
    """
    query = db.query(Interview)
    if candidate_id is not None:
        query = query.filter(Interview.candidate_id == candidate_id)
    if job_id is not None:
        query = query.filter(Interview.job_id == job_id)

    if current_user.role == "Candidate":
        candidate = db.query(Candidate).filter(Candidate.email == current_user.username).first()
        if not candidate:
            return []
        query = query.filter(Interview.candidate_id == candidate.id)

    interviews = query.all()
    return interviews


@router.get("/interview/{interview_id}", response_model=InterviewResponse)
@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
def get_interview_by_id(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_auth_checker)
):
    """
    Get interview details by ID.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID {interview_id} not found."
        )
    return interview


@router.put("/interview/{interview_id}", response_model=InterviewResponse)
@router.put("/interviews/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: int,
    interview_in: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_manager_checker)
):
    """
    Update interview details. Restricted to Recruiter, Hiring Manager, and Admin.
    """
    logger.info(f"Updating interview {interview_id}")
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID {interview_id} not found."
        )

    update_data = interview_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(interview, field, value)

    db.commit()
    db.refresh(interview)

    log_candidate_history(
        db, 
        interview.candidate_id, 
        "Interview Updated", 
        f"Updated interview details: {list(update_data.keys())}", 
        current_user.username
    )

    logger.info(f"Interview {interview_id} updated successfully")
    return interview


@router.delete("/interview/{interview_id}", status_code=status.HTTP_200_OK)
@router.delete("/interviews/{interview_id}", status_code=status.HTTP_200_OK)
def cancel_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_manager_checker)
):
    """
    Cancel / Delete an interview. Restricted to Recruiter, Hiring Manager, and Admin.
    """
    logger.info(f"Cancelling/Deleting interview {interview_id}")
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID {interview_id} not found."
        )

    candidate_id = interview.candidate_id
    db.delete(interview)
    db.commit()

    log_candidate_history(
        db, 
        candidate_id, 
        "Interview Cancelled", 
        f"Interview ID {interview_id} was cancelled/deleted", 
        current_user.username
    )

    logger.info(f"Interview {interview_id} deleted successfully.")
    return {"detail": f"Interview with ID {interview_id} deleted successfully."}

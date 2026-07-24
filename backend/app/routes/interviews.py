from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.models import Interview, Candidate
from app.schemas import InterviewCreate, InterviewResponse
from app.auth import RoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interviews"])

recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])
recruiter_manager_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])

VALID_PLATFORMS = ["Google Meet", "Microsoft Teams", "Zoom"]


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def schedule_interview(
    interview_in: InterviewCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_admin_checker),
):
    """
    Schedule a new interview for a shortlisted candidate.
    Restricted to Recruiters and Admins.
    """
    logger.info(f"Scheduling interview for candidate ID: {interview_in.candidate_id}")

    # Validate platform
    if interview_in.platform not in VALID_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform. Must be one of: {VALID_PLATFORMS}",
        )

    # Fetch candidate to denormalize name/email
    candidate = db.query(Candidate).filter(Candidate.id == interview_in.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {interview_in.candidate_id} not found.",
        )

    interview = Interview(
        candidate_id=interview_in.candidate_id,
        candidate_name=candidate.name,
        candidate_email=candidate.email,
        interview_date=interview_in.interview_date,
        interview_time=interview_in.interview_time,
        interviewer_name=interview_in.interviewer_name,
        platform=interview_in.platform,
        notes=interview_in.notes,
        status="Scheduled",
    )
    db.add(interview)

    # Also update candidate status to "Interview"
    candidate.status = "Interview"
    db.commit()
    db.refresh(interview)

    logger.info(f"Interview scheduled (ID: {interview.id}) for candidate {candidate.name}")
    return interview


@router.get("", response_model=List[InterviewResponse])
def list_interviews(
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_manager_admin_checker),
):
    """
    List all scheduled interviews.
    Accessible by Recruiters, Hiring Managers, and Admins.
    """
    logger.info("Fetching all scheduled interviews.")
    interviews = db.query(Interview).order_by(Interview.interview_date, Interview.interview_time).all()
    return interviews


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_manager_admin_checker),
):
    """
    Retrieve a single interview by ID.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID {interview_id} not found.",
        )
    return interview


@router.patch("/{interview_id}/status", response_model=InterviewResponse)
def update_interview_status(
    interview_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_manager_admin_checker),
):
    """
    Update the status of an interview (Scheduled / Completed / Cancelled).
    """
    valid_statuses = ["Scheduled", "Completed", "Cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID {interview_id} not found.",
        )

    interview.status = new_status
    db.commit()
    db.refresh(interview)
    logger.info(f"Interview {interview_id} status updated to {new_status}")
    return interview

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional, cast, Any
import logging
from datetime import datetime

from app.database import get_db
from app.models import Interview, Candidate, Job, CandidateHistory, InterviewSlot
from app.schemas import (
    InterviewCreate, InterviewUpdate, InterviewResponse,
    InterviewSlotCreate, InterviewSlotResponse, SlotBookRequest
)
from app.auth import RoleChecker, User
from app.services.redis_cache import invalidate_candidate, cache_candidate


logger = logging.getLogger(__name__)

router = APIRouter(tags=["interviews"])

recruiter_manager_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])

def log_candidate_history(db: Session, candidate_id: int, action: str, details: Optional[str] = None, performed_by: Optional[str] = None):
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
    db.commit()
    db.refresh(db_interview)

    # Automatically generate calendar invites & notifications
    try:
        from app.services.calendar import send_interview_notifications
        send_interview_notifications(db, db_interview, candidate, job)
    except Exception as e:
        logger.error(f"Failed to generate calendar invite: {str(e)}")

    # Update candidate status
    cast(Any, candidate).status = "Interview Scheduled"
    db.commit()
    db.refresh(db_interview)
    db.refresh(candidate)

    invalidate_candidate(int(cast(Any, candidate.id)))
    log_candidate_history(
        db, 
        int(cast(Any, candidate.id)), 
        "Interview Scheduled", 
        f"Scheduled interview with {interview_in.interviewer_name} at {interview_in.scheduled_time}", 
        str(current_user.username)
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

    current_user_any = cast(Any, current_user)
    if current_user_any.role == "Candidate":
        candidate = db.query(Candidate).filter(Candidate.email == current_user_any.username).first()
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
        int(cast(Any, interview.candidate_id)), 
        "Interview Updated", 
        f"Updated interview details: {list(update_data.keys())}", 
        str(current_user.username)
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
        int(cast(Any, candidate_id)), 
        "Interview Cancelled", 
        f"Interview ID {interview_id} was cancelled/deleted", 
        str(current_user.username)
    )

    logger.info(f"Interview {interview_id} deleted successfully.")
    return {"detail": f"Interview with ID {interview_id} deleted successfully."}


# --- Slot Management & iCal Download Endpoints ---

@router.get("/slots", response_model=List[InterviewSlotResponse])
@router.get("/interviews/slots", response_model=List[InterviewSlotResponse])
def list_available_slots(
    db: Session = Depends(get_db),
    _current_user: User = Depends(any_auth_checker)
):
    """
    List all available/unbooked interview slots.
    """
    return db.query(InterviewSlot).filter(InterviewSlot.is_booked == False).all()


@router.post("/slots", response_model=InterviewSlotResponse, status_code=status.HTTP_201_CREATED)
@router.post("/interviews/slots", response_model=InterviewSlotResponse, status_code=status.HTTP_201_CREATED)
def create_interview_slot(
    slot_in: InterviewSlotCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Create a new available interview slot.
    """
    slot = InterviewSlot(
        interviewer_name=slot_in.interviewer_name,
        interviewer_email=slot_in.interviewer_email,
        start_time=slot_in.start_time,
        end_time=slot_in.end_time,
        is_booked=False
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    logger.info(f"Created interview slot ID {slot.id} for {slot.interviewer_name}")
    return slot


@router.post("/slots/{slot_id}/book", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
@router.post("/interviews/slots/{slot_id}/book", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def book_interview_slot(
    slot_id: int,
    req: SlotBookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_manager_checker)
):
    """
    Book an available slot for a candidate and job.
    """
    slot = db.query(InterviewSlot).filter(InterviewSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Slot with ID {slot_id} not found.")
    
    if slot.is_booked is not None and bool(slot.is_booked):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot is already booked.")

    candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate with ID {req.candidate_id} not found.")

    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {req.job_id} not found.")

    # Create interview
    interview = Interview(
        candidate_id=req.candidate_id,
        job_id=req.job_id,
        interviewer_name=slot.interviewer_name,
        interviewer_email=slot.interviewer_email,
        scheduled_time=slot.start_time.isoformat(),
        duration_minutes=int((slot.end_time - slot.start_time).total_seconds() / 60),
        mode="Online",
        notes=f"Booked via slot ID {slot_id}",
        status="Scheduled"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # Link slot to interview and mark booked
    cast(Any, slot).is_booked = True
    cast(Any, slot).interview_id = interview.id
    db.commit()

    # Generate invite and send notifications
    try:
        from app.services.calendar import send_interview_notifications
        send_interview_notifications(db, interview, candidate, job)
    except Exception as e:
        logger.error(f"Failed to generate calendar invite: {str(e)}")

    # Update candidate status
    cast(Any, candidate).status = "Interview Scheduled"
    db.commit()
    db.refresh(candidate)

    invalidate_candidate(int(cast(Any, candidate.id)))
    log_candidate_history(
        db, 
        int(cast(Any, candidate.id)), 
        "Interview Scheduled (Slot Booked)", 
        f"Booked slot ID {slot_id} with {slot.interviewer_name} at {slot.start_time}", 
        str(current_user.username)
    )

    logger.info(f"Slot ID {slot_id} booked successfully. Interview ID: {interview.id}")
    return interview


@router.get("/interview/{interview_id}/invite")
@router.get("/interviews/{interview_id}/invite")
def download_calendar_invite(
    interview_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(any_auth_checker)
):
    """
    Download the .ics calendar invite for an interview.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Interview with ID {interview_id} not found.")
    
    # If the user is a Candidate, verify it's their own interview
    current_user_any = cast(Any, _current_user)
    if current_user_any.role == "Candidate":
        candidate = db.query(Candidate).filter(Candidate.email == current_user_any.username).first()
        if not candidate or int(cast(Any, interview.candidate_id)) != int(cast(Any, candidate.id)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    ics_content = str(interview.calendar_invite) if interview.calendar_invite is not None else None
    if ics_content is None or not ics_content:
        # Generate on the fly if not cached
        candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
        job = db.query(Job).filter(Job.id == interview.job_id).first()
        if candidate and job:
            from app.services.calendar import generate_ics_invite
            ics_content = generate_ics_invite(interview, candidate, job)
            cast(Any, interview).calendar_invite = ics_content
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate invite. Candidate or Job info missing.")

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=interview_{interview_id}.ics"
        }
    )


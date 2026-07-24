from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone

from app.database import get_db
from app.models import Candidate, CandidateHistory
from app.schemas import EmailRequest, EmailResponse
from app.auth import RoleChecker, User
from app.services.redis_cache import invalidate_candidate, cache_candidate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["emails"])

recruiter_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])

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

@router.post("/send-shortlist", response_model=EmailResponse, status_code=status.HTTP_200_OK)
def send_shortlist_email(
    request_in: EmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_checker)
):
    """
    Send shortlisting email notification to candidate and update candidate status to 'Shortlisted'.
    """
    candidate = db.query(Candidate).filter(Candidate.id == request_in.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {request_in.candidate_id} not found."
        )

    subject = request_in.subject or f"Congratulations {candidate.name}! You have been Shortlisted"
    body = request_in.message or (
        f"Dear {candidate.name},\n\n"
        "We are pleased to inform you that your application has been shortlisted. "
        "Our team will contact you shortly regarding next steps.\n\n"
        "Best regards,\nRecruiterAI Team"
    )

    logger.info(f"Sending shortlist email to {candidate.email}")
    
    # Update candidate status
    old_status = candidate.status
    candidate.status = "Shortlisted"
    db.commit()

    invalidate_candidate(candidate.id)
    log_candidate_history(
        db,
        candidate.id,
        "Shortlist Email Sent",
        f"Subject: {subject} | Updated status from {old_status} to Shortlisted",
        current_user.username
    )

    return EmailResponse(
        success=True,
        candidate_id=candidate.id,
        email_type="Shortlist",
        recipient=candidate.email,
        message=body,
        timestamp=datetime.now(timezone.utc)
    )


@router.post("/send-interview", response_model=EmailResponse, status_code=status.HTTP_200_OK)
def send_interview_email(
    request_in: EmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_checker)
):
    """
    Send interview invitation email to candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == request_in.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {request_in.candidate_id} not found."
        )

    subject = request_in.subject or f"Interview Invitation - RecruiterAI"
    body = request_in.message or (
        f"Dear {candidate.name},\n\n"
        "We would like to invite you for an interview. Please check your interview schedule details in your portal.\n\n"
        "Best regards,\nRecruiterAI Team"
    )

    logger.info(f"Sending interview email to {candidate.email}")

    log_candidate_history(
        db,
        candidate.id,
        "Interview Email Sent",
        f"Subject: {subject}",
        current_user.username
    )

    return EmailResponse(
        success=True,
        candidate_id=candidate.id,
        email_type="Interview Invitation",
        recipient=candidate.email,
        message=body,
        timestamp=datetime.now(timezone.utc)
    )


@router.post("/send-rejection", response_model=EmailResponse, status_code=status.HTTP_200_OK)
def send_rejection_email(
    request_in: EmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_checker)
):
    """
    Send rejection email notification to candidate and update candidate status to 'Rejected'.
    """
    candidate = db.query(Candidate).filter(Candidate.id == request_in.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {request_in.candidate_id} not found."
        )

    subject = request_in.subject or f"Update on your application with RecruiterAI"
    body = request_in.message or (
        f"Dear {candidate.name},\n\n"
        "Thank you for applying. After careful consideration, we have decided not to move forward with your application at this time.\n\n"
        "Best regards,\nRecruiterAI Team"
    )

    logger.info(f"Sending rejection email to {candidate.email}")

    # Update candidate status
    old_status = candidate.status
    candidate.status = "Rejected"
    db.commit()

    invalidate_candidate(candidate.id)
    log_candidate_history(
        db,
        candidate.id,
        "Rejection Email Sent",
        f"Subject: {subject} | Updated status from {old_status} to Rejected",
        current_user.username
    )

    return EmailResponse(
        success=True,
        candidate_id=candidate.id,
        email_type="Rejection",
        recipient=candidate.email,
        message=body,
        timestamp=datetime.now(timezone.utc)
    )


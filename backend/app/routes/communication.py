from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Candidate
from app.schemas import EmailResponse
from app.auth import RoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/communicate", tags=["communication"])

recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])


def _get_candidate_or_404(candidate_id: int, db: Session) -> Candidate:
    """Shared helper to fetch candidate or raise 404."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found.",
        )
    return candidate


@router.post("/shortlist/{candidate_id}", response_model=EmailResponse)
def send_shortlist_email(
    candidate_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_admin_checker),
):
    """
    Send a shortlist congratulations email to the candidate.
    Mock implementation — logs the action and returns a success response.
    Restricted to Recruiters and Admins.
    """
    candidate = _get_candidate_or_404(candidate_id, db)

    logger.info(
        f"[EMAIL MOCK] Shortlist email sent to {candidate.name} <{candidate.email}>"
    )

    # In a real system, integrate SendGrid / SMTP here
    email_body = (
        f"Dear {candidate.name},\n\n"
        "Congratulations! We are pleased to inform you that you have been shortlisted "
        "for the position you applied for. Our recruitment team will be in touch shortly "
        "to discuss next steps.\n\n"
        "Best regards,\nRecruiterAI Team"
    )
    logger.debug(f"[EMAIL MOCK] Body:\n{email_body}")

    return EmailResponse(
        success=True,
        message=f"Shortlist email successfully sent to {candidate.name} ({candidate.email}).",
        candidate_id=candidate_id,
        email_type="shortlist",
        recipient_email=candidate.email,
    )


@router.post("/interview/{candidate_id}", response_model=EmailResponse)
def send_interview_invitation(
    candidate_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_admin_checker),
):
    """
    Send an interview invitation email to the candidate.
    Mock implementation — logs the action and returns a success response.
    Restricted to Recruiters and Admins.
    """
    candidate = _get_candidate_or_404(candidate_id, db)

    logger.info(
        f"[EMAIL MOCK] Interview invitation sent to {candidate.name} <{candidate.email}>"
    )

    email_body = (
        f"Dear {candidate.name},\n\n"
        "We would like to invite you to an interview for the position you applied for. "
        "Please expect a calendar invite with the meeting details shortly. "
        "If you have any questions, feel free to reach out to our team.\n\n"
        "Best regards,\nRecruiterAI Team"
    )
    logger.debug(f"[EMAIL MOCK] Body:\n{email_body}")

    return EmailResponse(
        success=True,
        message=f"Interview invitation email successfully sent to {candidate.name} ({candidate.email}).",
        candidate_id=candidate_id,
        email_type="interview_invitation",
        recipient_email=candidate.email,
    )


@router.post("/reject/{candidate_id}", response_model=EmailResponse)
def send_rejection_email(
    candidate_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(recruiter_admin_checker),
):
    """
    Send a polite rejection email to the candidate.
    Mock implementation — logs the action and returns a success response.
    Restricted to Recruiters and Admins.
    """
    candidate = _get_candidate_or_404(candidate_id, db)

    logger.info(
        f"[EMAIL MOCK] Rejection email sent to {candidate.name} <{candidate.email}>"
    )

    email_body = (
        f"Dear {candidate.name},\n\n"
        "Thank you for your interest in our company and for taking the time to apply. "
        "After careful consideration, we regret to inform you that we will not be moving "
        "forward with your application at this time. We appreciate your effort and wish "
        "you the best in your job search.\n\n"
        "Best regards,\nRecruiterAI Team"
    )
    logger.debug(f"[EMAIL MOCK] Body:\n{email_body}")

    return EmailResponse(
        success=True,
        message=f"Rejection email successfully sent to {candidate.name} ({candidate.email}).",
        candidate_id=candidate_id,
        email_type="rejection",
        recipient_email=candidate.email,
    )

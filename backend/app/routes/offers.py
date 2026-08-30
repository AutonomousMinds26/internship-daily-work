from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth import RoleChecker, User as AuthUser
from app.models import Offer, Candidate, Job, CandidateActivity, CandidateHistory
from app.schemas import OfferCreate, OfferUpdate, OfferResponse
from app.services.email_service import render_email_template, send_email_notification

router = APIRouter(prefix="/offers", tags=["offers"])

recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])


@router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(
    offer_in: OfferCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(recruiter_admin_checker)
):
    """
    Create a new job offer for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == offer_in.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    job = db.query(Job).filter(Job.id == offer_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Generate template text if not provided
    offer_letter = offer_in.offer_letter_text or (
        f"Official Offer Letter\n\n"
        f"Dear {candidate.name},\n"
        f"We are delighted to offer you the position of {job.title} at our organization. "
        f"Your annual base compensation will be {offer_in.currency} {offer_in.base_salary:,.2f}.\n"
        f"We look forward to welcoming you to the team."
    )

    new_offer = Offer(
        candidate_id=offer_in.candidate_id,
        job_id=offer_in.job_id,
        base_salary=offer_in.base_salary,
        bonus=offer_in.bonus,
        stock_grant=offer_in.stock_grant,
        currency=offer_in.currency,
        status="Draft",
        offer_letter_text=offer_letter,
        expiration_date=offer_in.expiration_date,
        created_by=current_user.username
    )
    db.add(new_offer)

    # Transition candidate status
    candidate.status = "Offer Created"

    # Log Activity & History
    activity = CandidateActivity(
        candidate_id=candidate.id,
        activity_type="offer_created",
        description=f"Offer created: {offer_in.currency} {offer_in.base_salary:,.0f} by {current_user.username}",
        created_by=current_user.username
    )
    history = CandidateHistory(
        candidate_id=candidate.id,
        action="Offer Extended",
        details=f"Offer created with base salary {offer_in.currency} {offer_in.base_salary:,.0f}",
        performed_by=current_user.username
    )
    db.add(activity)
    db.add(history)
    db.commit()
    db.refresh(new_offer)

    return new_offer


@router.get("", response_model=List[OfferResponse])
def list_offers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(recruiter_admin_checker)
):
    """
    List all generated offers.
    """
    return db.query(Offer).order_by(desc(Offer.created_at)).offset(skip).limit(limit).all()


@router.get("/candidate/{candidate_id}", response_model=List[OfferResponse])
def get_candidate_offers(
    candidate_id: int,
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(recruiter_admin_checker)
):
    """
    Get all offers for a specific candidate.
    """
    return db.query(Offer).filter(Offer.candidate_id == candidate_id).all()


@router.put("/{id}", response_model=OfferResponse)
def update_offer(
    id: int,
    update_in: OfferUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(recruiter_admin_checker)
):
    """
    Update an offer (status: Sent, Accepted, Rejected, Expired, or modify compensation).
    """
    offer = db.query(Offer).filter(Offer.id == id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if update_in.base_salary is not None:
        offer.base_salary = update_in.base_salary
    if update_in.bonus is not None:
        offer.bonus = update_in.bonus
    if update_in.stock_grant is not None:
        offer.stock_grant = update_in.stock_grant
    if update_in.currency is not None:
        offer.currency = update_in.currency
    if update_in.expiration_date is not None:
        offer.expiration_date = update_in.expiration_date
    if update_in.offer_letter_text is not None:
        offer.offer_letter_text = update_in.offer_letter_text

    if update_in.status is not None:
        old_status = offer.status
        offer.status = update_in.status

        # Synchronize candidate status
        candidate = db.query(Candidate).filter(Candidate.id == offer.candidate_id).first()
        if candidate:
            if update_in.status == "Accepted":
                candidate.status = "Hired"
            elif update_in.status == "Sent":
                candidate.status = "Offered"
            elif update_in.status == "Rejected":
                candidate.status = "Offer Declined"

            activity = CandidateActivity(
                candidate_id=candidate.id,
                activity_type="offer_status_change",
                description=f"Offer #{offer.id} status changed from {old_status} to {update_in.status}",
                created_by=current_user.username
            )
            db.add(activity)

    db.commit()
    db.refresh(offer)
    return offer

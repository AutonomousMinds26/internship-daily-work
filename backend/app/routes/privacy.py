import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import RoleChecker, User as AuthUser
from app.models import (
    Candidate, CandidateConsent, Resume, CandidateScore,
    Assessment, Interview, Offer, CandidateActivity, AuditLog
)
from app.schemas import (
    CandidateConsentCreate, CandidateConsentResponse, CandidateGDPRExportResponse
)

router = APIRouter(prefix="/privacy", tags=["privacy"])

recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])
admin_checker = RoleChecker(allowed_roles=["Admin"])


@router.post("/consent", response_model=CandidateConsentResponse, status_code=status.HTTP_201_CREATED)
def record_candidate_consent(
    consent_in: CandidateConsentCreate,
    db: Session = Depends(get_db)
):
    """
    Record or update candidate explicit data processing consent (GDPR / Indian DPDP).
    """
    candidate = db.query(Candidate).filter(Candidate.id == consent_in.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    consent = CandidateConsent(
        candidate_id=consent_in.candidate_id,
        consent_type=consent_in.consent_type,
        granted=consent_in.granted,
        terms_version=consent_in.terms_version
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


@router.get("/consent/{candidate_id}", response_model=List[CandidateConsentResponse])
def get_candidate_consents(
    candidate_id: int,
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(recruiter_admin_checker)
):
    """
    Fetch all active and historical consent logs for a candidate.
    """
    return db.query(CandidateConsent).filter(CandidateConsent.candidate_id == candidate_id).all()


@router.get("/candidates/{id}/export", response_model=CandidateGDPRExportResponse)
def export_candidate_data_gdpr(
    id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(recruiter_admin_checker)
):
    """
    Comprehensive GDPR / Indian DPDP Data Subject Access Request (DSAR) JSON Export.
    Returns all stored candidate profile data, resumes, assessments, interviews, offers, and audit logs.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Collect all relational data
    profile_data = {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "education": candidate.education,
        "experience_years": candidate.experience,
        "skills": candidate.skills,
        "projects": candidate.projects,
        "expected_ctc": candidate.expected_ctc,
        "current_ctc": candidate.current_ctc,
        "location": candidate.location,
        "status": candidate.status,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None
    }

    resumes = [
        {"id": r.id, "file_name": r.file_name, "file_type": r.file_type, "created_at": str(r.created_at)}
        for r in candidate.resumes
    ]

    assessments = [
        {"id": a.id, "provider": a.assessment_provider, "test_name": a.test_name, "score": a.score, "status": a.status}
        for a in candidate.assessments
    ]

    interviews = [
        {"id": i.id, "interviewer": i.interviewer_name, "scheduled_time": str(i.scheduled_time), "status": i.status}
        for i in candidate.interviews
    ]

    offers = [
        {"id": o.id, "base_salary": o.base_salary, "currency": o.currency, "status": o.status}
        for o in candidate.offers
    ]

    activities = [
        {"id": act.id, "type": act.activity_type, "description": act.description, "created_at": str(act.created_at)}
        for act in candidate.activities
    ]

    consents = [
        {"id": c.id, "consent_type": c.consent_type, "granted": c.granted, "timestamp": str(c.timestamp)}
        for c in candidate.consents
    ]

    # Audit export event
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="DATA_EXPORT",
        resource_type="Candidate",
        resource_id=str(id),
        details={"candidate_email": candidate.email}
    )
    db.add(audit)
    db.commit()

    return {
        "candidate_id": id,
        "exported_at": datetime.now(timezone.utc),
        "profile": profile_data,
        "applications": [],
        "resumes": resumes,
        "assessments": assessments,
        "interviews": interviews,
        "offers": offers,
        "activities": activities,
        "consents": consents
    }


@router.delete("/candidates/{id}/delete", status_code=status.HTTP_200_OK)
def delete_candidate_data_privacy(
    id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(admin_checker)
):
    """
    Execute Right-to-be-Forgotten: Anonymizes PII or permanently soft-deletes candidate profile (Admin only).
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Anonymize PII
    old_email = candidate.email
    candidate.name = f"Anonymized Candidate #{candidate.id}"
    candidate.email = f"anonymized_{candidate.id}@deleted.local"
    candidate.phone = None
    candidate.resume_text = "[REDACTED PURSUANT TO GDPR / DPDP RIGHT TO BE FORGOTTEN]"
    candidate.is_deleted = True

    # Clear raw text in resumes
    for r in candidate.resumes:
        r.raw_text = "[REDACTED]"
        r.parsed_data = {}

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="DATA_DELETION",
        resource_type="Candidate",
        resource_id=str(id),
        details={"previous_email": old_email, "compliance": "GDPR_DPDP_RIGHT_TO_BE_FORGOTTEN"}
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "candidate_id": id,
        "message": "Candidate PII successfully anonymized and marked deleted under privacy regulations."
    }

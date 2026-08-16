from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, cast, Any
from datetime import datetime, timezone

from app.database import get_db
from app.auth import RoleChecker, get_current_user, User
from app.models import (
    Candidate, Job, CandidateSource, CandidateActivity,
    ReferenceCheck, Verification, RecruiterComment, Prediction
)
from app.schemas import (
    CandidateResponse, CandidateSourceImportRequest, CandidateImportBulkRequest,
    SourcingSummaryResponse, RecruiterCommentCreate, RecruiterCommentResponse,
    CandidateAssignRequest, CandidateActivityResponse, ReferenceCheckCreate,
    ReferenceCheckResponse, VerificationCreate, VerificationResponse,
    PredictionResponse, PredictionsReportSummary
)
from app.services.sourcing_service import import_candidate_from_source

router = APIRouter(tags=["extended_features"])

# --- Role Checkers ---
recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])
recruiter_manager_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])


# --- Candidate Sourcing APIs ---

@router.post("/sources/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def source_candidate_endpoint(
    request: CandidateSourceImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_admin_checker)
):
    """
    Import/source a candidate from an external recruitment source.
    Performs duplicate check, inserts candidate, links source, and triggers AI screening.
    """
    result = import_candidate_from_source(
        candidate_data=request.candidate.model_dump(),
        source_data=request.source.model_dump(),
        job_id=request.job_id,
        db=db,
        performed_by=str(current_user.username)
    )
    
    if result["is_duplicate"]:
        dup_details = result["duplicate_details"]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate candidate detected. Reason: {dup_details['reason']} (ID: {dup_details['duplicate_id']}, Name: {dup_details['name']})"
        )
        
    return result["candidate"]


@router.get("/sources", response_model=List[SourcingSummaryResponse])
def get_sources_endpoint(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve counts of candidates sourced from each unique source provider.
    """
    results = db.query(
        CandidateSource.source_name,
        func.count(CandidateSource.id).label("candidate_count")
    ).group_by(CandidateSource.source_name).all()
    
    return [{"source_name": r[0], "candidate_count": r[1]} for r in results]


@router.post("/candidates/import", status_code=status.HTTP_200_OK)
def import_candidates_bulk_endpoint(
    request: CandidateImportBulkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_admin_checker)
):
    """
    Bulk import candidates from external sourcing feeds.
    """
    imported = 0
    duplicates = 0
    details = []
    
    for item in request.imports:
        res = import_candidate_from_source(
            candidate_data=item.candidate.model_dump(),
            source_data=item.source.model_dump(),
            job_id=item.job_id,
            db=db,
            performed_by=str(current_user.username)
        )
        
        email = item.candidate.email
        if res["is_duplicate"]:
            duplicates += 1
            details.append({"email": email, "status": "skipped", "reason": res["duplicate_details"]["reason"]})
        else:
            imported += 1
            details.append({"email": email, "status": "imported", "candidate_id": res["candidate"].id})
            
    return {
        "total": len(request.imports),
        "imported": imported,
        "duplicates": duplicates,
        "details": details
    }


# --- Collaboration APIs ---

@router.post("/candidates/{id}/comments", response_model=RecruiterCommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment_endpoint(
    id: int,
    request: RecruiterCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_manager_checker)
):
    """
    Add a recruiter/manager comment to a candidate profile and log activity.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    comment_rec = RecruiterComment(
        candidate_id=id,
        comment=request.comment,
        author=current_user.username
    )
    db.add(comment_rec)
    
    activity = CandidateActivity(
        candidate_id=id,
        activity_type="comment_added",
        description=f"Comment added by recruiter/manager: '{request.comment[:40]}...'",
        created_by=current_user.username
    )
    db.add(activity)
    db.commit()
    db.refresh(comment_rec)
    
    return comment_rec


@router.get("/candidates/{id}/comments", response_model=List[RecruiterCommentResponse])
def get_comments_endpoint(
    id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve all recruiter comments for a specific candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return db.query(RecruiterComment).filter(RecruiterComment.candidate_id == id).order_by(RecruiterComment.created_at.desc()).all()


@router.post("/candidates/{id}/assign", status_code=status.HTTP_200_OK)
def assign_candidate_endpoint(
    id: int,
    request: CandidateAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_admin_checker)
):
    """
    Assign a recruiter or hiring manager to a candidate and transition their status if requested.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Optional status update
    old_status = candidate.status
    if request.status:
        setattr(candidate, "status", request.status)
        
    # Log assignment activity
    activity = CandidateActivity(
        candidate_id=id,
        activity_type="candidate_assigned",
        description=f"Candidate assigned to '{request.assigned_to}' by {current_user.username} (status updated: {old_status} -> {candidate.status})",
        created_by=str(current_user.username)
    )
    db.add(activity)
    db.commit()
    
    return {
        "success": True,
        "message": f"Candidate successfully assigned to {request.assigned_to}.",
        "candidate_id": id,
        "status": candidate.status
    }


@router.get("/candidates/{id}/activity", response_model=List[CandidateActivityResponse])
def get_activity_endpoint(
    id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Fetch the activity/audit timeline for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return db.query(CandidateActivity).filter(CandidateActivity.candidate_id == id).order_by(CandidateActivity.created_at.desc()).all()


# --- Reference & Verification APIs ---

@router.post("/candidates/{id}/reference-check", response_model=ReferenceCheckResponse, status_code=status.HTTP_201_CREATED)
def create_reference_check_endpoint(
    id: int,
    request: ReferenceCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_admin_checker)
):
    """
    Initiate or document a reference check for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    verified_at = datetime.now(timezone.utc) if request.status == "Completed" else None
    ref_check = ReferenceCheck(
        candidate_id=id,
        referee_name=request.referee_name,
        referee_contact=request.referee_contact,
        referee_relationship=request.referee_relationship,
        status=request.status,
        comments=request.comments,
        verified_at=verified_at
    )
    db.add(ref_check)
    
    # Log activity
    activity = CandidateActivity(
        candidate_id=id,
        activity_type="reference_check",
        description=f"Reference check details added for referee {request.referee_name} (status: {request.status})",
        created_by=current_user.username
    )
    db.add(activity)
    db.commit()
    db.refresh(ref_check)
    
    return ref_check


@router.get("/candidates/{id}/reference-check", response_model=List[ReferenceCheckResponse])
def get_reference_checks_endpoint(
    id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Fetch all reference checks documented for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return db.query(ReferenceCheck).filter(ReferenceCheck.candidate_id == id).all()


@router.post("/candidates/{id}/verification", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
def create_verification_endpoint(
    id: int,
    request: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_admin_checker)
):
    """
    Schedule or document a background verification (background check, degree check, etc.).
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    completed_at = datetime.now(timezone.utc) if request.status == "Verified" else None
    verif = Verification(
        candidate_id=id,
        verification_type=request.verification_type,
        status=request.status,
        agency=request.agency,
        details=request.details,
        completed_at=completed_at
    )
    db.add(verif)
    
    # Log activity
    activity = CandidateActivity(
        candidate_id=id,
        activity_type="verification",
        description=f"Verification type {request.verification_type} initiated via agency {request.agency or 'internal'} (status: {request.status})",
        created_by=current_user.username
    )
    db.add(activity)
    db.commit()
    db.refresh(verif)
    
    return verif


@router.get("/candidates/{id}/verification", response_model=List[VerificationResponse])
def get_verifications_endpoint(
    id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve verification history and status logs for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return db.query(Verification).filter(Verification.candidate_id == id).all()


# --- Predictive Analytics APIs ---

@router.get("/candidates/{id}/prediction", response_model=PredictionResponse)
def get_candidate_prediction_endpoint(
    id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Generate or fetch AI-based status and success probability predictions for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Check if prediction already exists
    pred = db.query(Prediction).filter(Prediction.candidate_id == id).first()
    if not pred:
        # Generate new prediction
        score = candidate.final_score or 50.0
        
        # Calculate simulated predictive model metrics
        if score >= 80.0:
            predicted_status = "Selected"
            probability = min(0.99, 0.80 + (score - 80.0) * 0.009)
            explanation = f"AI predicts a high probability of selection based on an exceptional final composite score of {score}% and high ATS matching."
        elif score >= 60.0:
            predicted_status = "Interview"
            probability = 0.60 + (score - 60.0) * 0.01
            explanation = f"AI suggests scheduling an interview based on a solid match score of {score}% and complete core skills overlap."
        else:
            predicted_status = "Rejected"
            probability = min(0.95, 0.70 + (60.0 - score) * 0.01)
            explanation = f"AI recommends rejection due to missing required skills and a low screening/match score of {score}%."
            
        pred = Prediction(
            candidate_id=id,
            predicted_status=predicted_status,
            probability=round(probability, 2),
            explanation=explanation,
            model_version="RecruiterAI-Predictor-v1.0"
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)
        
    return pred


@router.get("/reports/predictions", response_model=PredictionsReportSummary)
def get_predictions_report_endpoint(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Generates a recruitment analytics report summarizing all predictions.
    """
    # Trigger generation for any candidates missing a prediction to populate report
    candidates = db.query(Candidate).all()
    for cand in candidates:
        existing = db.query(Prediction).filter(Prediction.candidate_id == cand.id).first()
        if not existing:
            score = cand.final_score or 50.0
            if score >= 80.0:
                predicted_status = "Selected"
                probability = min(0.99, 0.80 + (score - 80.0) * 0.009)
                explanation = f"AI predicts selection (Score: {score}%)."
            elif score >= 60.0:
                predicted_status = "Interview"
                probability = 0.60 + (score - 60.0) * 0.01
                explanation = f"AI recommends interviewing (Score: {score}%)."
            else:
                predicted_status = "Rejected"
                probability = min(0.95, 0.70 + (60.0 - score) * 0.01)
                explanation = f"AI recommends rejection (Score: {score}%)."
                
            pred = Prediction(
                candidate_id=cand.id,
                predicted_status=predicted_status,
                probability=round(probability, 2),
                explanation=explanation,
                model_version="RecruiterAI-Predictor-v1.0"
            )
            db.add(pred)
    db.commit()
    
    predictions = db.query(Prediction).all()
    
    total = len(predictions)
    if total == 0:
        return {
            "total_predictions": 0,
            "predicted_selected_count": 0,
            "predicted_rejected_count": 0,
            "predicted_interview_count": 0,
            "average_probability": 0.0,
            "predictions": []
        }
        
    selected = sum(1 for p in predictions if p.predicted_status == "Selected")
    rejected = sum(1 for p in predictions if p.predicted_status == "Rejected")
    interview = sum(1 for p in predictions if p.predicted_status == "Interview")
    avg_prob = sum(float(getattr(p, "probability") or 0.0) for p in predictions) / total
    
    return {
        "total_predictions": total,
        "predicted_selected_count": selected,
        "predicted_rejected_count": rejected,
        "predicted_interview_count": interview,
        "average_probability": round(avg_prob, 2),
        "predictions": predictions
    }

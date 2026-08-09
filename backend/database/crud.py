from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from database.models import Candidate, Job

# Candidate CRUD Operations

def get_candidate(db: Session, candidate_id: int):
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()

def get_candidate_by_email(db: Session, email: str):
    return db.query(Candidate).filter(Candidate.email == email).first()

def get_candidates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Candidate).offset(skip).limit(limit).all()

def create_candidate(db: Session, candidate_data: dict):
    # Ensure scores defaults
    candidate_data.setdefault("ats_score", 0.0)
    candidate_data.setdefault("match_score", 0.0)
    candidate_data.setdefault("screening_score", 0.0)
    candidate_data.setdefault("final_score", 0.0)
    candidate_data.setdefault("status", "Applied")
    
    db_candidate = Candidate(**candidate_data)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def update_candidate(db: Session, candidate_id: int, update_data: dict):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None
    for key, value in update_data.items():
        setattr(db_candidate, key, value)
    db_candidate.updated_at = func.now()
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def delete_candidate(db: Session, candidate_id: int):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None
    db.delete(db_candidate)
    db.commit()
    return db_candidate

def update_candidate_status(db: Session, candidate_id: int, status: str):
    db_candidate = get_candidate(db, candidate_id)
    if not db_candidate:
        return None
    db_candidate.status = status
    db_candidate.updated_at = func.now()
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

# Report Helpers

def get_reports_summary(db: Session):
    total = db.query(Candidate).count()
    applied = db.query(Candidate).filter(Candidate.status == "Applied").count()
    screening = db.query(Candidate).filter(Candidate.status == "Screening").count()
    shortlisted = db.query(Candidate).filter(Candidate.status == "Shortlisted").count()
    interview = db.query(Candidate).filter(Candidate.status == "Interview").count()
    selected = db.query(Candidate).filter(Candidate.status == "Selected").count()
    rejected = db.query(Candidate).filter(Candidate.status == "Rejected").count()
    
    return {
        "total_candidates": total,
        "applied": applied,
        "screening": screening,
        "shortlisted": shortlisted,
        "interviewed": interview,
        "selected": selected,
        "rejected": rejected
    }

def get_reports_candidates(db: Session):
    candidates = db.query(Candidate).all()
    result = []
    for c in candidates:
        result.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "status": c.status,
            "ats_score": c.ats_score,
            "match_score": c.match_score,
            "screening_score": c.screening_score,
            "final_score": c.final_score,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        })
    return result

def get_reports_status(db: Session):
    statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Selected", "Rejected"]
    distribution = {}
    for status in statuses:
        count = db.query(Candidate).filter(Candidate.status == status).count()
        distribution[status] = count
    return {
        "status_distribution": distribution
    }

def get_reports_scores(db: Session):
    candidates = db.query(Candidate).order_by(Candidate.final_score.desc()).all()
    if not candidates:
        return {
            "average_ats_score": 0.0,
            "average_match_score": 0.0,
            "average_screening_score": 0.0,
            "average_final_score": 0.0,
            "score_distribution": []
        }
    
    avg_ats = db.query(func.avg(Candidate.ats_score)).scalar() or 0.0
    avg_match = db.query(func.avg(Candidate.match_score)).scalar() or 0.0
    avg_screening = db.query(func.avg(Candidate.screening_score)).scalar() or 0.0
    avg_final = db.query(func.avg(Candidate.final_score)).scalar() or 0.0
    
    distribution = []
    for c in candidates:
        distribution.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "ats_score": c.ats_score,
            "match_score": c.match_score,
            "screening_score": c.screening_score,
            "final_score": c.final_score
        })
        
    return {
        "average_ats_score": round(avg_ats, 2),
        "average_match_score": round(avg_match, 2),
        "average_screening_score": round(avg_screening, 2),
        "average_final_score": round(avg_final, 2),
        "score_distribution": distribution
    }

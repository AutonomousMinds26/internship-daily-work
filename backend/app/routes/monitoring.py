from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.database import get_db
from app.models import User, Candidate, Job, Interview, CandidateScore, Recommendation
from app.schemas import HealthResponse, StatusResponse, MetricsResponse
from app.services.redis_cache import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """
    Check system health, database connectivity, and Redis connectivity.
    """
    db_status = "healthy"
    try:
        db.execute(func.now()).fetchone()
    except Exception as e:
        logger.error(f"Health check DB failed: {str(e)}")
        db_status = f"unhealthy: {str(e)}"

    redis_status = "healthy"
    if redis_client is not None:
        try:
            redis_client.ping()
        except Exception as e:
            logger.warning(f"Health check Redis ping failed: {str(e)}")
            redis_status = "unavailable"
    else:
        redis_status = "disabled/unavailable"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status
    )


@router.get("/status", response_model=StatusResponse, status_code=status.HTTP_200_OK)
def get_system_status(db: Session = Depends(get_db)):
    """
    Retrieve overall system operational status and entity counts.
    """
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_interviews = db.query(func.count(Interview.id)).scalar() or 0

    return StatusResponse(
        status="running",
        service="RecruiterAI Backend API",
        version="1.0.0",
        total_users=total_users,
        total_candidates=total_candidates,
        total_jobs=total_jobs,
        total_interviews=total_interviews
    )


@router.get("/metrics", response_model=MetricsResponse, status_code=status.HTTP_200_OK)
def get_recruitment_metrics(db: Session = Depends(get_db)):
    """
    Retrieve recruitment pipeline analytics and candidate status metrics.
    """
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_interviews = db.query(func.count(Interview.id)).scalar() or 0
    total_scores = db.query(func.count(CandidateScore.id)).scalar() or 0

    # Group candidate counts by status
    status_counts_raw = (
        db.query(Candidate.status, func.count(Candidate.id))
        .group_by(Candidate.status)
        .all()
    )
    candidates_by_status = {st: count for st, count in status_counts_raw}

    # Ensure all standard statuses are present in metrics dict
    standard_statuses = ["Applied", "Parsed", "Matched", "Shortlisted", "Interview Scheduled", "Selected", "Rejected"]
    for s in standard_statuses:
        if s not in candidates_by_status:
            candidates_by_status[s] = 0

    return MetricsResponse(
        total_candidates=total_candidates,
        candidates_by_status=candidates_by_status,
        total_jobs=total_jobs,
        total_interviews=total_interviews,
        total_scores=total_scores
    )


@router.get("/analytics", response_model=dict, status_code=status.HTTP_200_OK)
def get_analytics(db: Session = Depends(get_db)):
    """
    Retrieve comprehensive recruitment statistics and dataset representations for dashboard charts.
    """
    logger.info("Computing recruitment dashboard analytics.")
    
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    shortlisted_candidates = db.query(func.count(Candidate.id)).filter(Candidate.status == "Shortlisted").scalar() or 0
    rejected_candidates = db.query(func.count(Candidate.id)).filter(Candidate.status == "Rejected").scalar() or 0
    
    # Compute average match score over all candidate score evaluations
    avg_match = db.query(func.avg(CandidateScore.match_score)).scalar()
    average_match_percentage = round(float(avg_match), 1) if avg_match is not None else 0.0
    
    # Pending interviews are scheduled ones
    pending_interviews = db.query(func.count(Interview.id)).filter(Interview.status == "Scheduled").scalar() or 0
    
    # Get all match scores for Match Percentage Distribution
    scores = db.query(CandidateScore.match_score).all()
    match_percentages = [float(s[0]) for s in scores]
    
    # Group recommendation count (Shortlist, Maybe, Reject)
    recs = db.query(Recommendation.recommendation, func.count(Recommendation.id)).group_by(Recommendation.recommendation).all()
    recommendation_counts = {r[0]: r[1] for r in recs}
    
    # Parse candidate skills list to count skill frequencies
    candidates = db.query(Candidate.skills).all()
    skills_counts = {}
    for c in candidates:
        if c[0] and isinstance(c[0], list):
            for skill in c[0]:
                skill_clean = skill.strip()
                if skill_clean:
                    skill_title = skill_clean.title()
                    skills_counts[skill_title] = skills_counts.get(skill_title, 0) + 1
                    
    # Return top 15 skills
    sorted_skills = sorted(skills_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    skills_distribution = {k: v for k, v in sorted_skills}
    
    # Hiring funnel counts: Applied -> Parsed -> Matched -> Shortlisted -> Interview -> Selected
    status_counts_raw = db.query(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status).all()
    status_counts = {s[0]: s[1] for s in status_counts_raw}
    
    # Funnel stages: Applied, Parsed, Matched, Shortlisted, Interview, Selected
    funnel = {
        "Applied": status_counts.get("Applied", 0) + status_counts.get("Screening", 0),
        "Parsed": status_counts.get("Parsed", 0),
        "Matched": status_counts.get("Matched", 0),
        "Shortlisted": status_counts.get("Shortlisted", 0),
        "Interview": status_counts.get("Interview Scheduled", 0) + status_counts.get("Interview", 0),
        "Selected": status_counts.get("Selected", 0)
    }
    
    return {
        "total_candidates": total_candidates,
        "shortlisted_candidates": shortlisted_candidates,
        "rejected_candidates": rejected_candidates,
        "average_match_percentage": average_match_percentage,
        "pending_interviews": pending_interviews,
        "match_percentages": match_percentages,
        "recommendation_counts": recommendation_counts,
        "skills_distribution": skills_distribution,
        "hiring_funnel": funnel
    }

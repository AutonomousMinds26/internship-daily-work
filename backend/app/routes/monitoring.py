from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.database import get_db
from app.models import User, Candidate, Job, Interview, CandidateScore
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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobResponse
from app.auth import RoleChecker

from app.services.redis_cache import get_cached_job, cache_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])

# Allowed roles: Recruiter, Admin
recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])

def serialize_job(j: Job) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "description": j.description,
        "requirements": j.requirements,
        "experience_required": j.experience_required,
        "created_at": j.created_at.isoformat() if j.created_at else None
    }

@router.post("/job", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    _current_user = Depends(recruiter_admin_checker)
):
    """
    Create a new job requirement. Access is restricted to Recruiters and Admins.
    """
    logger.info(f"Creating job: {job_in.title}")
    db_job = Job(
        title=job_in.title,
        description=job_in.description,
        requirements=job_in.requirements,
        experience_required=job_in.experience_required
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    cache_job(db_job.id, serialize_job(db_job))
    logger.info(f"Job created successfully with ID: {db_job.id}")
    return db_job


@router.get("/job", response_model=List[JobResponse])
@router.get("/jobs", response_model=List[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    _current_user = Depends(any_auth_checker)
):
    """
    Get all jobs. Access permitted for Recruiters, Hiring Managers, Admins, and Candidates.
    """
    logger.info("Retrieving all jobs from DB.")
    jobs = db.query(Job).all()
    return jobs


@router.get("/job/{job_id}", response_model=JobResponse)
@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
    _current_user = Depends(any_auth_checker)
):
    """
    Get a job by ID (uses Redis cache).
    """
    cached_job = get_cached_job(job_id)
    if cached_job:
        return cached_job

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    cache_job(job_id, serialize_job(job))
    return job



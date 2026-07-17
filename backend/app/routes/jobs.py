from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobResponse
from app.auth import RoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job", tags=["jobs"])

# Allowed roles: Recruiter, Admin
recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
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
    logger.info(f"Job created successfully with ID: {db_job.id}")
    return db_job

@router.get("", response_model=List[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    _current_user = Depends(any_auth_checker)
):
    """
    Get all jobs. Access permitted for Recruiters, Hiring Managers, and Admins.
    """
    logger.info("Retrieving all jobs from DB.")
    jobs = db.query(Job).all()
    return jobs


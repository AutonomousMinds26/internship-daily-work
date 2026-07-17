from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import fitz  # PyMuPDF
import logging
from datetime import datetime

from app.database import get_db
from app.models import Candidate, Job
from app.schemas import CandidateResponse, ScoreResponse, MatchDetails
from app.auth import RoleChecker, get_current_user, User
from app.services.extractor import extract_candidate_info
from app.services.redis_cache import get_cached_candidate, cache_candidate, invalidate_candidate
from app.services.matcher import calculate_match_score

logger = logging.getLogger(__name__)

router = APIRouter(tags=["candidates"])

# Endpoints authorization checkers
recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])

def serialize_candidate(c: Candidate) -> dict:
    """Helper to convert Candidate model to dict for Redis caching."""
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "education": c.education,
        "experience": c.experience,
        "skills": c.skills,
        "projects": c.projects,
        "notice_period": c.notice_period,
        "expected_ctc": c.expected_ctc,
        "location": c.location,
        "resume_text": c.resume_text,
        "created_at": c.created_at.isoformat() if c.created_at else datetime.utcnow().isoformat()
    }

@router.post("/upload_resume", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user = Depends(recruiter_admin_checker)
):
    """
    Upload resume (PDF or TXT), extract text, parse details, and save to DB.
    Access restricted to Recruiters and Admins.
    """
    logger.info(f"Resume upload initiated: {file.filename}")
    filename = file.filename.lower()
    
    if filename.endswith(".pdf"):
        try:
            contents = await file.read()
            doc = fitz.open(stream=contents, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            logger.error(f"Failed parsing PDF {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse PDF resume: {str(e)}"
            )
    elif filename.endswith(".txt"):
        try:
            contents = await file.read()
            text = contents.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed parsing TXT {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse TXT resume: {str(e)}"
            )
    else:
        logger.warning(f"Unsupported file type uploaded: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF and TXT resumes are supported."
        )

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded resume is empty."
        )

    # Extract info using service
    info = extract_candidate_info(text)
    info["resume_text"] = text

    # Verify if email extraction succeeded
    if not info["email"]:
        # Fallback default unique email if not found in resume
        info["email"] = f"unknown_{int(datetime.utcnow().timestamp())}@recruiterai.com"

    # Check if candidate email already exists
    candidate = db.query(Candidate).filter(Candidate.email == info["email"]).first()
    
    if candidate:
        logger.info(f"Updating existing candidate: {info['email']}")
        candidate.name = info["name"]
        candidate.phone = info["phone"]
        candidate.education = info["education"]
        candidate.experience = info["experience"]
        candidate.skills = info["skills"]
        candidate.projects = info["projects"]
        candidate.notice_period = info["notice_period"]
        candidate.expected_ctc = info["expected_ctc"]
        candidate.location = info["location"]
        candidate.resume_text = info["resume_text"]
    else:
        logger.info(f"Creating new candidate: {info['email']}")
        candidate = Candidate(**info)
        db.add(candidate)
        
    db.commit()
    db.refresh(candidate)

    # Invalidate cache if it existed, and cache the new data
    invalidate_candidate(candidate.id)
    cand_dict = serialize_candidate(candidate)
    cache_candidate(candidate.id, cand_dict)

    logger.info(f"Resume processed successfully for candidate {candidate.name} (ID: {candidate.id})")
    return candidate

@router.get("/candidate", response_model=None)
def get_candidate(
    id: Optional[int] = None,
    db: Session = Depends(get_db),
    _current_user = Depends(any_auth_checker)
):
    """
    Get all candidates or retrieve a single candidate (uses cache-aside strategy).
    Access permitted for Recruiters, Hiring Managers, and Admins.
    """
    if id is not None:
        # Cache-aside lookup
        cached_cand = get_cached_candidate(id)
        if cached_cand:
            return cached_cand

        # Fallback to DB
        candidate = db.query(Candidate).filter(Candidate.id == id).first()
        if not candidate:
            logger.warning(f"Candidate {id} not found in DB.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {id} not found."
            )
        
        # Cache and return
        cand_dict = serialize_candidate(candidate)
        cache_candidate(id, cand_dict)
        return candidate
    else:
        # Return all candidates
        logger.info("Retrieving all candidates from DB.")
        candidates = db.query(Candidate).all()
        return candidates

@router.get("/score", response_model=ScoreResponse)
def get_score(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user = Depends(any_auth_checker)
):
    """
    Calculate and retrieve candidate compatibility score against a job.
    Access permitted for Recruiters, Hiring Managers, and Admins.
    """
    logger.info(f"Calculating match score: Candidate {candidate_id} vs Job {job_id}")
    
    # Try fetching candidate (cache-aside friendly)
    candidate_data = get_cached_candidate(candidate_id)
    if candidate_data:
        # Recreate list objects/experience from cache
        cand_skills = candidate_data["skills"]
        cand_exp = candidate_data["experience"]
    else:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found."
            )
        cand_skills = candidate.skills
        cand_exp = candidate.experience
        # Cache candidate for future use
        cache_candidate(candidate_id, serialize_candidate(candidate))

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    score, matched, missing, gap = calculate_match_score(
        cand_skills,
        job.requirements,
        cand_exp,
        job.experience_required
    )

    logger.info(f"Match calculation complete. Score: {score}")
    return ScoreResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        match_score=score,
        details=MatchDetails(
            matched_skills=matched,
            missing_skills=missing,
            experience_gap=gap
        )
    )

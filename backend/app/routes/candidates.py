from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import fitz  # PyMuPDF
import logging
from datetime import datetime

from app.database import get_db
from app.models import Candidate, Job
from app.schemas import CandidateResponse, ScoreResponse, MatchDetails, CandidateStatusUpdate, UploadResumeResponse
from app.auth import RoleChecker, get_current_user, User
from app.services.extractor import extract_candidate_info
from app.services.redis_cache import get_cached_candidate, cache_candidate, invalidate_candidate
from app.services.matcher import calculate_match_score

logger = logging.getLogger(__name__)

router = APIRouter(tags=["candidates"])

# Endpoints authorization checkers
recruiter_admin_checker = RoleChecker(allowed_roles=["Recruiter", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])
status_update_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])

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
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else datetime.utcnow().isoformat()
    }

@router.post("/upload_resume", response_model=UploadResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    job_id: Optional[int] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user = Depends(recruiter_admin_checker)
):
    """
    Upload resume (PDF or TXT), select Job Role, fetch Job Description, 
    extract candidate details, extract job details, run AI matcher, 
    save results, and return JSON.
    Access restricted to Recruiters and Admins.
    """
    logger.info(f"Resume upload initiated: {file.filename} for job {job_id}")
    
    # 1. Fetch Job from DB
    if job_id is None:
        job = db.query(Job).first()
        if not job:
            logger.info("No jobs found in DB. Creating a default fallback Job.")
            job = Job(
                title="Default Job Role",
                description="Default Fallback Job Description",
                requirements=["Python"],
                experience_required=0
            )
            db.add(job)
            db.commit()
            db.refresh(job)
        job_id = job.id
    else:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.warning(f"Job {job_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found."
            )

    # 2. Extract text from uploaded file
    filename = file.filename.lower()
    text = ""
    if filename.endswith(".pdf"):
        try:
            contents = await file.read()
            doc = fitz.open(stream=contents, filetype="pdf")
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

    # 3. Setup path and imports for AI pipeline
    import sys
    import os
    
    ai_dir = os.path.join(os.path.dirname(__file__), "..", "..", "AI")
    if ai_dir not in sys.path:
        sys.path.append(ai_dir)
        
    ai_extract_candidate = None
    ai_extract_job = None
    ai_match_candidate = None
    extract_years = None

    try:
        from resume_extractor import extract_candidate_info as ai_extract_candidate
        from job_extractor import extract_job_info as ai_extract_job
        from ai_matcher import ai_match_candidate
        from scorer import extract_years
    except Exception as e:
        logger.warning(f"AI pipeline modules could not be loaded: {str(e)}")

    # 4. Extract Candidate Info
    candidate_info = None
    if ai_extract_candidate is not None:
        try:
            candidate_info = ai_extract_candidate(text)
        except Exception as e:
            logger.error(f"AI candidate extraction failed: {str(e)}")

    if candidate_info is None:
        logger.info("Using regex candidate extraction fallback.")
        candidate_info = extract_candidate_info(text) # fallback regex service
        
    candidate_info["resume_text"] = text

    # Handle experience string parsing for integer field in candidate DB
    experience_years = 0
    if "experience" in candidate_info:
        exp_val = candidate_info["experience"]
        if isinstance(exp_val, int):
            experience_years = exp_val
        elif isinstance(exp_val, str) and exp_val.isdigit():
            experience_years = int(exp_val)
        elif extract_years is not None:
            try:
                experience_years = extract_years(str(exp_val))
            except Exception:
                experience_years = 0
        else:
            import re
            match = re.search(r'(\d+)', str(exp_val))
            experience_years = int(match.group(1)) if match else 0

    candidate_info["experience"] = f"{experience_years} years"

    # Ensure basic fields are populated
    email = candidate_info.get("email") or f"unknown_{int(datetime.utcnow().timestamp())}@recruiterai.com"
    name = candidate_info.get("name") or "Unknown Candidate"

    # 5. Extract Job Info
    job_info = None
    if ai_extract_job is not None:
        job_text = f"Job Title: {job.title}\nJob Description: {job.description}\nRequired Skills: {', '.join(job.requirements)}\nRequired Experience: {job.experience_required} years"
        try:
            job_info = ai_extract_job(job_text)
        except Exception as e:
            logger.error(f"AI job extraction failed: {str(e)}")

    if job_info is None:
        job_info = {
            "job_title": job.title,
            "required_skills": job.requirements,
            "experience": f"{job.experience_required} years",
            "location": "",
            "salary_range": "",
            "notice_period": ""
        }

    # 6. Run Matcher
    match_result = None
    if ai_match_candidate is not None:
        try:
            match_result = ai_match_candidate(candidate_info, job_info)
        except Exception as e:
            logger.error(f"AI matching failed: {str(e)}")

    if match_result is None:
        logger.info("Using Python scorer fallback.")
        try:
            from scorer import calculate_score
            match_result = calculate_score(candidate_info, job_info)
        except Exception as e:
            logger.error(f"Fallback Python scorer import failed: {str(e)}")
            candidate_skills = {s.lower() for s in candidate_info.get("skills", [])}
            required_skills = {s.lower() for s in job_info.get("required_skills", [])}
            matched_skills = list(candidate_skills & required_skills)
            missing_skills = list(required_skills - candidate_skills)
            match_pct = int((len(matched_skills) / len(required_skills) * 100)) if required_skills else 0
            rec_val = "Shortlisted" if match_pct >= 70 else "Applied"
            match_result = {
                "candidate": name,
                "email": email,
                "match_percentage": match_pct,
                "matched_skills": [s for s in candidate_info.get("skills", []) if s.lower() in matched_skills],
                "missing_skills": [s for s in job_info.get("required_skills", []) if s.lower() in missing_skills],
                "strengths": [],
                "weaknesses": [],
                "recommendation": rec_val
            }

    # Ensure strengths and weaknesses lists exist
    strengths = match_result.get("strengths") or []
    weaknesses = match_result.get("weaknesses") or []

    # Map recommendation to valid statuses: ["Applied", "Screening", "Shortlisted", "Interview", "Selected"]
    rec = match_result.get("recommendation", "Applied")
    status_val = "Applied"

    # 7. Save Candidate to DB
    # Handle fields format
    skills_list = candidate_info.get("skills", [])
    if isinstance(skills_list, str):
        skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]
        
    projects_list = candidate_info.get("projects", [])
    if isinstance(projects_list, str):
        projects_list = [p.strip() for p in projects_list.split(",") if p.strip()]

    candidate_db = db.query(Candidate).filter(Candidate.email == email).first()
    
    candidate_db_data = {
        "name": name,
        "email": email,
        "phone": candidate_info.get("phone"),
        "education": candidate_info.get("education"),
        "experience": experience_years,
        "skills": skills_list,
        "projects": projects_list,
        "notice_period": candidate_info.get("notice_period"),
        "expected_ctc": candidate_info.get("expected_ctc"),
        "location": candidate_info.get("location"),
        "resume_text": text,
        "status": status_val
    }

    if candidate_db:
        logger.info(f"Updating existing candidate: {email}")
        for k, v in candidate_db_data.items():
            setattr(candidate_db, k, v)
    else:
        logger.info(f"Creating new candidate: {email}")
        candidate_db = Candidate(**candidate_db_data)
        db.add(candidate_db)
        
    db.commit()
    db.refresh(candidate_db)

    # Invalidate cache if it existed, and cache the new data
    invalidate_candidate(candidate_db.id)
    cand_dict = serialize_candidate(candidate_db)
    cache_candidate(candidate_db.id, cand_dict)

    logger.info(f"Resume processed and matched successfully for candidate {name} (ID: {candidate_db.id})")
    
    # 8. Return JSON with candidate details for test compatibility
    return {
        "candidate": name,
        "email": email,
        "match_percentage": match_result.get("match_percentage", 0),
        "matched_skills": match_result.get("matched_skills", []),
        "missing_skills": match_result.get("missing_skills", []),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": rec,
        "id": candidate_db.id,
        "name": name,
        "phone": candidate_info.get("phone"),
        "experience": experience_years,
        "skills": skills_list,
        "location": candidate_info.get("location"),
        "notice_period": candidate_info.get("notice_period"),
        "expected_ctc": candidate_info.get("expected_ctc"),
        "status": status_val
    }

@router.get("/candidate", response_model=None)
def get_candidate(
    id: Optional[int] = None,
    db: Session = Depends(get_db),
    _current_user = Depends(any_auth_checker)
):
    """
    Get all candidates or retrieve a single candidate (uses cache-aside strategy).
    Access permitted for Recruiters, Hiring Managers, Admins, and Candidates (restricted to self).
    """
    if _current_user.role == "Candidate":
        if id is not None:
            # Check if this candidate ID matches current user's email
            cached_cand = get_cached_candidate(id)
            if cached_cand:
                if cached_cand["email"] != _current_user.username:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to other candidates' profiles."
                    )
                return cached_cand
            
            candidate = db.query(Candidate).filter(Candidate.id == id).first()
            if not candidate:
                logger.warning(f"Candidate {id} not found in DB.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate with ID {id} not found."
                )
            if candidate.email != _current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to other candidates' profiles."
                )
            cand_dict = serialize_candidate(candidate)
            cache_candidate(id, cand_dict)
            return candidate
        else:
            # Candidate gets only their own profile
            logger.info(f"Candidate {_current_user.username} retrieving their own profile.")
            candidate = db.query(Candidate).filter(Candidate.email == _current_user.username).first()
            return [candidate] if candidate else []

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
    Access permitted for Recruiters, Hiring Managers, Admins, and Candidates (restricted to self).
    """
    logger.info(f"Calculating match score: Candidate {candidate_id} vs Job {job_id}")
    
    # Try fetching candidate (cache-aside friendly)
    candidate_data = get_cached_candidate(candidate_id)
    if candidate_data:
        # Recreate list objects/experience from cache
        cand_skills = candidate_data["skills"]
        cand_exp = candidate_data["experience"]
        cand_email = candidate_data["email"]
    else:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found."
            )
        cand_skills = candidate.skills
        cand_exp = candidate.experience
        cand_email = candidate.email
        # Cache candidate for future use
        cache_candidate(candidate_id, serialize_candidate(candidate))

    # Candidate security check
    if _current_user.role == "Candidate" and cand_email != _current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to other candidates' scores."
        )

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

@router.patch("/candidate/{candidate_id}/status", response_model=CandidateResponse)
def update_candidate_status(
    candidate_id: int,
    status_in: CandidateStatusUpdate,
    db: Session = Depends(get_db),
    _current_user = Depends(status_update_checker)
):
    """
    Update candidate status. Restricted to Recruiter, Hiring Manager, and Admin.
    """
    logger.info(f"Updating candidate {candidate_id} status to {status_in.status}")
    valid_statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Selected"]
    if status_in.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {valid_statuses}."
        )
    
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        logger.warning(f"Candidate {candidate_id} not found for status update.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )
        
    candidate.status = status_in.status
    db.commit()
    db.refresh(candidate)
    
    # Invalidate cache and write back
    invalidate_candidate(candidate.id)
    cache_candidate(candidate.id, serialize_candidate(candidate))
    
    logger.info(f"Candidate {candidate_id} status updated successfully to {status_in.status}")
    return candidate


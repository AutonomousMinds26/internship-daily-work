import os
import re
import shutil
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional, cast, Any
from datetime import datetime

import fitz  # PyMuPDF

# Import new database package elements
from database.database import engine, get_db, Base
import database.models as models
import database.crud as crud

# Import AI Scorers
from AI.scorer import calculate_enhanced_score, extract_years

# Ensure SQLite database tables are created/updated
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RecruiterAI Candidate Pipeline API",
    description="Backend API implementing candidate pipeline database operations, status progression, resume screening, and recruitment reports.",
    version="1.1.0"
)

# --- Pydantic Schemas ---

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: Optional[str] = None # Comma-separated list of skills
    education: Optional[str] = None
    experience: int = 0
    notice_period: Optional[str] = None
    location: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_CTC: Optional[str] = None
    resume_path: Optional[str] = None

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    ats_score: Optional[float] = None
    match_score: Optional[float] = None
    screening_score: Optional[float] = None
    final_score: Optional[float] = None
    status: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[int] = None
    notice_period: Optional[str] = None
    location: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_CTC: Optional[str] = None

class CandidateStatusUpdate(BaseModel):
    status: str

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    ats_score: float
    match_score: float
    screening_score: float
    final_score: float
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Compatibility fields
    skills: Optional[str] = None
    education: Optional[str] = None
    experience: int
    notice_period: Optional[str] = None
    location: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_CTC: Optional[str] = None
    score: float

    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    job_title: str
    required_skills: str
    experience: int = 0
    location: Optional[str] = None
    salary_range: Optional[str] = None
    notice_period_requirement: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    job_title: str
    required_skills: str
    experience: int
    location: Optional[str] = None
    salary_range: Optional[str] = None
    notice_period_requirement: Optional[str] = None

    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    candidate_name: str
    skill_match: str
    recommendation: str

class ScreeningResponse(BaseModel):
    candidate_id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    ats_score: float
    match_score: float
    screening_score: float
    final_score: float
    status: str
    extracted_info: dict

# Valid Status values in candidate pipeline
VALID_STATUSES = ["Applied", "Screening", "Shortlisted", "Interview", "Selected", "Rejected"]

@app.get("/")
def home():
    return {"message": "Welcome to RecruiterAI Backend Candidate Pipeline API"}

# --- A2-6. Candidate Pipeline APIs ---

@app.post("/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate_in: CandidateCreate, db: Session = Depends(get_db)):
    # Check if candidate email already exists
    existing = crud.get_candidate_by_email(db, candidate_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate with this email already exists."
        )
    
    candidate_data = candidate_in.model_dump()
    # Populate legacy compatibility score field from default final_score (0.0)
    candidate_data["score"] = 0.0
    
    db_candidate = crud.create_candidate(db, candidate_data)
    return db_candidate

@app.get("/candidates", response_model=List[CandidateResponse])
def get_candidates(db: Session = Depends(get_db)):
    return crud.get_candidates(db)

@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = crud.get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )
    return db_candidate

@app.put("/candidates/{candidate_id}", response_model=CandidateResponse)
def update_candidate(candidate_id: int, candidate_in: CandidateUpdate, db: Session = Depends(get_db)):
    db_candidate = crud.get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )
    
    update_data = candidate_in.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {VALID_STATUSES}"
        )
    
    # If final_score is updated, update the compatibility score field too
    if "final_score" in update_data:
        update_data["score"] = update_data["final_score"]
        
    updated = crud.update_candidate(db, candidate_id, update_data)
    return updated

@app.delete("/candidates/{candidate_id}", status_code=status.HTTP_200_OK)
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    db_candidate = crud.get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )
    crud.delete_candidate(db, candidate_id)
    return {"detail": f"Candidate with ID {candidate_id} deleted successfully."}

@app.put("/candidates/{candidate_id}/status", response_model=CandidateResponse)
def update_candidate_status_api(candidate_id: int, status_in: CandidateStatusUpdate, db: Session = Depends(get_db)):
    if status_in.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {VALID_STATUSES}"
        )
    
    db_candidate = crud.get_candidate(db, candidate_id)
    if not db_candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )
        
    updated = crud.update_candidate_status(db, candidate_id, status_in.status)
    return updated

# --- A2-7. Screening API ---

@app.post("/screen-resume", response_model=ScreeningResponse)
async def screen_resume(
    file: UploadFile = File(...),
    job_id: Optional[int] = Form(None),
    job_description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # 1. Save upload file
    upload_dir = "sample_resumes"
    os.makedirs(upload_dir, exist_ok=True)
    filename = file.filename or "resume.txt"
    resume_path = os.path.join(upload_dir, filename)
    
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Read text
    text = ""
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):

        try:
            doc = fitz.open(resume_path)
            for page in doc:
                text += str(page.get_text())
            doc.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF resume: {str(e)}")
    else:
        try:
            with open(resume_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse text resume: {str(e)}")
            
    if not text.strip():
        raise HTTPException(status_code=400, detail="The uploaded resume file is empty.")

    # 2. AI Screening Extraction
    candidate_info = None
    try:
        from AI.resume_extractor import extract_candidate_info as ai_extract
        candidate_info = ai_extract(text)
    except Exception:
        pass
        
    # Fallback to pattern regex extractor if LLM extractor fails or returns invalid
    if not candidate_info or candidate_info.get("name") == "Not Available":
        candidate_info = {}
        # Name fallback
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        candidate_info["name"] = lines[0] if lines else "Unknown Candidate"
        # Email fallback
        import time
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        candidate_info["email"] = email_match.group(0) if email_match else f"unknown_{int(time.time())}@example.com"
        # Phone fallback
        phone_match = re.search(r'\+?\d[\d -]{8,12}\d', text)
        candidate_info["phone"] = phone_match.group(0) if phone_match else None
        # Skills fallback
        skills_match = re.findall(r'(python|fastapi|sql|docker|javascript|java|aws|kubernetes|c\+\+|html|css|git|react)', text, re.IGNORECASE)
        candidate_info["skills"] = list(set(skills_match)) if skills_match else []
        # Experience fallback
        exp_match = re.search(r'(\d+)\+?\s*(years|year|yrs)', text, re.IGNORECASE)
        candidate_info["experience"] = int(exp_match.group(1)) if exp_match else 0
        # Education fallback
        edu_keywords = ["b.tech", "b.e", "m.tech", "bachelor", "master", "ph.d", "doctor", "mca", "bca", "bsc", "msc"]
        found_edu = [kw for kw in edu_keywords if kw in text.lower()]
        candidate_info["education"] = ", ".join(found_edu).upper() if found_edu else "Not Specified"
        candidate_info["projects"] = []
        candidate_info["notice_period"] = "Not Available"
        candidate_info["expected_ctc"] = "Not Available"
        candidate_info["location"] = "Not Available"

    import time
    name = candidate_info.get("name") or "Unknown Candidate"
    email = candidate_info.get("email") or f"unknown_{int(time.time())}@example.com"
    phone = candidate_info.get("phone")
    education_val = str(candidate_info.get("education") or "Not Available")

    
    # Process experience field
    raw_exp = candidate_info.get("experience", 0)
    experience_years = extract_years(raw_exp)
    
    # Process skills field
    raw_skills = candidate_info.get("skills", [])
    if isinstance(raw_skills, list):
        skills_str = ", ".join(raw_skills)
        skills_list = raw_skills
    else:
        skills_str = str(raw_skills)
        skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]

    # Projects list
    projects_list = candidate_info.get("projects", [])
    if isinstance(projects_list, str):
        projects_list = [p.strip() for p in projects_list.split(",") if p.strip()]

    # Notice period, CTC, Location
    notice_period_val = candidate_info.get("notice_period") or "Not Available"
    expected_ctc_val = candidate_info.get("expected_ctc") or "Not Available"
    location_val = candidate_info.get("location") or "Not Available"

    # ATS score will be calculated below after job_dict is constructed

    
    # 4. Fetch Job and Calculate Match Score
    job = None
    if job_id:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        # Fallback to first job in SQLite
        job = db.query(models.Job).first()
    if not job:
        # Create a default fallback job in database so matching is successful
        job = models.Job(
            job_title="Software Engineer",
            required_skills="Python, SQL, FastAPI",
            experience=2,
            location="Remote",
            salary_range="10-15 LPA",
            notice_period_requirement="30 days"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    # Calculate enhanced Match Score
    cand_dict = {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills_list,
        "education": education_val,
        "experience": experience_years,
        "projects": projects_list,
        "notice_period": notice_period_val,
        "expected_ctc": expected_ctc_val,
        "location": location_val
    }
    
    job_skills_list = [s.strip() for s in job.required_skills.split(",") if s.strip()] if isinstance(job.required_skills, str) else job.required_skills
    job_dict = {
        "job_title": job.job_title,
        "required_skills": job_skills_list,
        "experience": job.experience,
        "salary_range": job.salary_range
    }
    
    # Calculate ATS score using ats_analyzer
    from AI.ats_analyzer import analyze_ats
    cand_dict_ats = dict(cand_dict)
    cand_dict_ats["resume_text"] = text
    ats_res = analyze_ats(cand_dict_ats, job_dict)
    ats_score = float(ats_res.get("ats_score", 0.0))

    score_details = calculate_enhanced_score(cand_dict, job_dict)
    match_score = float(score_details.get("match_percentage", 50.0))


    # 5. Calculate Screening Score
    screening_score = 0.0
    # Experience match: 40 pts
    if experience_years >= job.experience:
        screening_score += 40
    elif job.experience - experience_years <= 1:
        screening_score += 30
    elif job.experience - experience_years <= 2:
        screening_score += 20
    else:
        screening_score += 10
        
    # Skills match: 40 pts
    job_skills_norm = {s.lower().strip() for s in job_skills_list}
    cand_skills_norm = {s.lower().strip() for s in skills_list}
    matched_skills_count = len(job_skills_norm & cand_skills_norm)
    if job_skills_norm:
        skills_ratio = matched_skills_count / len(job_skills_norm)
        screening_score += (skills_ratio * 40)
    else:
        screening_score += 40
        
    # Education: 20 pts
    edu_lower = education_val.lower()
    if any(kw in edu_lower for kw in ["ph.d", "doctor", "master", "m.tech", "mca"]):
        screening_score += 20
    elif any(kw in edu_lower for kw in ["b.tech", "b.e", "bachelor", "bsc", "bca"]):
        screening_score += 15
    else:
        screening_score += 10

    # 6. Calculate Final Score
    final_score = round((0.3 * ats_score) + (0.5 * match_score) + (0.2 * screening_score), 2)

    # Save to Database
    candidate_db_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "resume_path": resume_path,
        "ats_score": ats_score,
        "match_score": match_score,
        "screening_score": screening_score,
        "final_score": final_score,
        "status": "Applied",
        "skills": skills_str,
        "education": education_val,
        "experience": experience_years,
        "notice_period": notice_period_val,
        "location": location_val,
        "preferred_location": location_val,
        "expected_CTC": expected_ctc_val,
        "score": final_score  # compatibility with old score field
    }

    # Check if candidate exists, update if so, otherwise create
    email_str = str(email)
    existing_cand = crud.get_candidate_by_email(db, email_str)
    if existing_cand:
        db_candidate = crud.update_candidate(db, cast(Any, existing_cand.id), candidate_db_data)
    else:
        db_candidate = crud.create_candidate(db, candidate_db_data)

    if not db_candidate:
        raise HTTPException(status_code=500, detail="Failed to save candidate to database")

    db_cand = cast(Any, db_candidate)
    return {
        "candidate_id": db_cand.id,
        "name": db_cand.name,
        "email": db_cand.email,
        "phone": db_cand.phone,
        "ats_score": db_cand.ats_score,
        "match_score": db_cand.match_score,
        "screening_score": db_cand.screening_score,
        "final_score": db_cand.final_score,
        "status": db_cand.status,
        "extracted_info": candidate_info
    }




# --- A2-8. Recruitment Reports API ---

@app.get("/reports/summary")
def get_reports_summary_api(db: Session = Depends(get_db)):
    return crud.get_reports_summary(db)

@app.get("/reports/candidates")
def get_reports_candidates_api(db: Session = Depends(get_db)):
    return crud.get_reports_candidates(db)

@app.get("/reports/status")
def get_reports_status_api(db: Session = Depends(get_db)):
    return crud.get_reports_status(db)

@app.get("/reports/scores")
def get_reports_scores_api(db: Session = Depends(get_db)):
    return crud.get_reports_scores(db)

# --- Legacy Match Endpoint Compatibility ---

@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    db_job = models.Job(**job_in.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@app.get("/jobs", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(models.Job).all()

@app.get("/match", response_model=MatchResult)
def match_candidate(candidate_id: int, job_id: int, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    from matcher import calculate_skill_match, get_matching_recommendation
    
    match_percentage = calculate_skill_match(str(candidate.skills or ""), str(job.required_skills or ""))
    recommendation = get_matching_recommendation(match_percentage)
 
    setattr(candidate, "score", match_percentage)
    setattr(candidate, "match_score", match_percentage)
    db.commit()
    db.refresh(candidate)


    return {
        "candidate_name": candidate.name,
        "skill_match": f"{match_percentage}%",
        "recommendation": recommendation
    }

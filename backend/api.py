from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

import models
from database import engine, get_db, Base
from matcher import calculate_skill_match, get_matching_recommendation

# Initialize SQLite database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RecruiterAI Foundation API",
    description="FastAPI project structure at root backend",
    version="1.0.0"
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

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    experience: int
    notice_period: Optional[str] = None
    location: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_CTC: Optional[str] = None
    resume_path: Optional[str] = None
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

# --- Endpoints ---

@app.get("/")
def home():
    return {"message": "Welcome to RecruiterAI Backend Foundation"}

@app.post("/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate_in: CandidateCreate, db: Session = Depends(get_db)):
    # Check if email exists
    existing = db.query(models.Candidate).filter(models.Candidate.email == candidate_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate with this email already exists."
        )
    
    db_candidate = models.Candidate(**candidate_in.model_dump())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@app.get("/candidates", response_model=List[CandidateResponse])
def get_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).all()

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

    # Match skills and update candidate score in DB
    match_percentage = calculate_skill_match(candidate.skills, job.required_skills)
    recommendation = get_matching_recommendation(match_percentage)

    # Save calculated score to DB
    candidate.score = match_percentage
    db.commit()
    db.refresh(candidate)

    return {
        "candidate_name": candidate.name,
        "skill_match": f"{match_percentage}%",
        "recommendation": recommendation
    }

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = Field(..., description="Must be one of: Recruiter, Hiring Manager, Admin")

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# --- Job Schemas ---
class JobCreate(BaseModel):
    title: str
    description: str
    requirements: List[str] = []
    experience_required: int = 0

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    requirements: List[str]
    experience_required: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Candidate Schemas ---
class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: int = 0
    skills: List[str] = []
    projects: List[str] = []
    notice_period: Optional[str] = None
    expected_ctc: Optional[str] = None
    location: Optional[str] = None
    resume_text: Optional[str] = None
    status: Optional[str] = "Applied"

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: int
    skills: List[str]
    projects: List[str]
    notice_period: Optional[str] = None
    expected_ctc: Optional[str] = None
    location: Optional[str] = None
    resume_text: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateStatusUpdate(BaseModel):
    status: str


# --- Score/Match Schemas ---
class MatchDetails(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    experience_gap: int

class ScoreResponse(BaseModel):
    candidate_id: int
    job_id: int
    match_score: float
    details: MatchDetails

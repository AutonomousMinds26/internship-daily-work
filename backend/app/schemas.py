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
    ats_score: Optional[int] = 85
    screening_score: Optional[int] = 80
    final_score: Optional[int] = 82
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []
    ai_recommendation: Optional[str] = None
    candidate_summary: Optional[str] = None
    screening_responses: Optional[List[dict]] = []
    feedback: Optional[str] = None

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
    ats_score: Optional[int] = 85
    screening_score: Optional[int] = 80
    final_score: Optional[int] = 82
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []
    ai_recommendation: Optional[str] = None
    candidate_summary: Optional[str] = None
    screening_responses: Optional[List[dict]] = []
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateStatusUpdate(BaseModel):
    status: str

class CandidateFeedbackUpdate(BaseModel):
    feedback: str


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


# --- Interview Schemas ---
class InterviewCreate(BaseModel):
    candidate_id: int
    interview_date: str  # YYYY-MM-DD
    interview_time: str  # HH:MM
    interviewer_name: str
    platform: str  # Google Meet / Microsoft Teams / Zoom
    notes: Optional[str] = None

class InterviewResponse(BaseModel):
    id: int
    candidate_id: int
    candidate_name: str
    candidate_email: str
    interview_date: str
    interview_time: str
    interviewer_name: str
    platform: str
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Communication Schemas ---
class EmailRequest(BaseModel):
    candidate_id: int
    custom_message: Optional[str] = None

class EmailResponse(BaseModel):
    success: bool
    message: str
    candidate_id: int
    email_type: str
    recipient_email: str

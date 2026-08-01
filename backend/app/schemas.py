from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = Field(..., description="Must be one of: Recruiter, Hiring Manager, Admin")

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    created_at: datetime

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    requirements: List[str]
    experience_required: int
    created_at: datetime

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

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[int] = None
    skills: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    notice_period: Optional[str] = None
    expected_ctc: Optional[str] = None
    location: Optional[str] = None
    resume_text: Optional[str] = None
    status: Optional[str] = None

class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    ai_summary: Optional[str] = None
    resume_hash: Optional[str] = None

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
    skill_gap_report: Optional[dict] = None

class UploadResumeResponse(BaseModel):
    candidate: str
    email: str
    match_percentage: int
    matched_skills: List[str]
    missing_skills: List[str]
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendation: str
    id: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    experience: Optional[int] = 0
    skills: Optional[List[str]] = []
    location: Optional[str] = None
    notice_period: Optional[str] = None
    expected_ctc: Optional[str] = None
    status: Optional[str] = None
    ai_summary: Optional[str] = None
    resume_hash: Optional[str] = None


# --- Interview Schemas ---
class InterviewCreate(BaseModel):
    candidate_id: int
    job_id: int
    interviewer_name: str
    interviewer_email: EmailStr
    scheduled_time: str
    duration_minutes: Optional[int] = 45
    mode: Optional[str] = "Online"
    meeting_link: Optional[str] = None
    notes: Optional[str] = None

class InterviewUpdate(BaseModel):
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[EmailStr] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    mode: Optional[str] = None
    meeting_link: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    interviewer_name: str
    interviewer_email: EmailStr
    scheduled_time: str
    duration_minutes: int
    mode: str
    meeting_link: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

# --- Email Communication Schemas ---
class EmailRequest(BaseModel):
    candidate_id: int
    subject: Optional[str] = None
    message: Optional[str] = None

class EmailResponse(BaseModel):
    success: bool
    candidate_id: int
    email_type: str
    recipient: str
    message: str
    timestamp: datetime

# --- Candidate History Schemas ---
class CandidateHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    action: str
    details: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: datetime

# --- Monitoring Schemas ---
class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str

class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    total_users: int
    total_candidates: int
    total_jobs: int
    total_interviews: int

class MetricsResponse(BaseModel):
    total_candidates: int
    candidates_by_status: dict
    total_jobs: int
    total_interviews: int
    total_scores: int

# --- New Table & AI Responses Schemas ---

class InterviewQuestionCreate(BaseModel):
    candidate_id: int
    job_id: int
    question: str
    expected_answer: Optional[str] = None
    category: Optional[str] = "Technical"

class InterviewQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    question: str
    expected_answer: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime

class InterviewSlotCreate(BaseModel):
    interviewer_name: str
    interviewer_email: EmailStr
    start_time: datetime
    end_time: datetime

class InterviewSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interviewer_name: str
    interviewer_email: EmailStr
    start_time: datetime
    end_time: datetime
    is_booked: bool
    interview_id: Optional[int] = None

class SlotBookRequest(BaseModel):
    candidate_id: int
    job_id: int

# --- AI API Responses ---

class AISummaryResponse(BaseModel):
    candidate_id: int
    name: str
    ai_summary: str

class SkillGapResponse(BaseModel):
    candidate_id: int
    job_id: int
    matched_skills: List[str]
    missing_skills: List[str]
    experience_gap: int
    recommendations: List[str]

class InterviewQuestionsResponse(BaseModel):
    candidate_id: int
    job_id: int
    questions: List[InterviewQuestionResponse]

class ExplainableRecommendationResponse(BaseModel):
    candidate_id: int
    job_id: int
    recommendation: str
    strengths: List[str]
    weaknesses: List[str]
    justification: str

class SemanticMatchResponse(BaseModel):
    candidate_id: int
    job_id: int
    semantic_score: float
    matching_highlights: List[str]

# --- Analytics Response Schemas ---

class LocationDistributionResponse(BaseModel):
    location_distribution: dict

class ExperienceDistributionResponse(BaseModel):
    experience_distribution: dict

class EducationDistributionResponse(BaseModel):
    education_distribution: dict

class FunnelResponse(BaseModel):
    hiring_funnel: dict

class DiversityResponse(BaseModel):
    gender_distribution: dict
    university_distribution: dict

# --- Recruitment Tools Response Schemas ---

class ResumeScreeningResponse(BaseModel):
    candidate_id: int
    job_id: int
    passed_screening: bool
    experience_check: bool
    skills_match_percentage: float
    reasons: List[str]

class AssessmentQuestion(BaseModel):
    question: str
    category: str
    difficulty: str

class AssessmentGenerateResponse(BaseModel):
    candidate_id: int
    job_id: int
    test_id: str
    assessment_questions: List[AssessmentQuestion]

class AssessmentEvaluateRequest(BaseModel):
    candidate_id: int
    job_id: int
    answers: List[dict] # List of {"question": "...", "answer": "..."}

class AssessmentEvaluateResponse(BaseModel):
    candidate_id: int
    job_id: int
    score: float
    passed: bool
    evaluation_summary: str





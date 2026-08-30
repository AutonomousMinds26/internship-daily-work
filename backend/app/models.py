from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey, Boolean, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# --- Multi-tenancy & Teams ---

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    domain = Column(String, nullable=True)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    hiring_teams = relationship("HiringTeam", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")
    jobs = relationship("Job", back_populates="organization")


class HiringTeam(Base):
    __tablename__ = "hiring_teams"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    lead_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_hiring_team_lead"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    organization = relationship("Organization", back_populates="hiring_teams")
    members = relationship("User", back_populates="hiring_team", foreign_keys="User.hiring_team_id")
    jobs = relationship("Job", back_populates="hiring_team")


# --- Identity & Access Management ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    hiring_team_id = Column(Integer, ForeignKey("hiring_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Recruiter, Hiring Manager, Admin, Candidate
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="users")
    hiring_team = relationship("HiringTeam", back_populates="members", foreign_keys=[hiring_team_id])
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


# --- Core Requisitions & Jobs ---

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    hiring_team_id = Column(Integer, ForeignKey("hiring_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False, index=True)
    department = Column(String, default="Engineering", nullable=False, index=True)
    location = Column(String, default="Remote", nullable=False)
    employment_type = Column(String, default="Full-Time")  # Full-Time, Part-Time, Contract
    min_salary = Column(Float, nullable=True)
    max_salary = Column(Float, nullable=True)
    salary_currency = Column(String, default="INR")  # INR, USD, EUR
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=[])       # List of required skills
    nice_to_have = Column(JSON, default=[])       # Secondary skills
    experience_required = Column(Integer, default=0, index=True) # Years required
    status = Column(String, default="Open", index=True)  # Open, Closed, Draft, On Hold
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="jobs")
    hiring_team = relationship("HiringTeam", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    scores = relationship("CandidateScore", back_populates="job", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="job", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="job", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="job", cascade="all, delete-orphan")


# --- Talent & Candidate Profiles ---

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    education = Column(Text, nullable=True)
    experience = Column(Integer, default=0, index=True)  # Years of experience
    skills = Column(JSON, default=[])         # List of skills
    projects = Column(JSON, default=[])       # List of projects
    notice_period = Column(String, nullable=True)
    expected_ctc = Column(String, nullable=True)
    current_ctc = Column(String, nullable=True)
    location = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    status = Column(String, default="Applied", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Extended intelligence & evaluation fields
    ai_summary = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    resume_hash = Column(String, unique=True, index=True, nullable=True)
    ats_score = Column(Float, default=0.0)
    match_score = Column(Float, default=0.0)
    screening_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    ats_details = Column(JSON, nullable=True)

    # Demographic & Indian Market details (for bias audits & localized parsing)
    gender = Column(String, nullable=True)  # Optional / self-declared for 4/5ths analysis
    ethnicity = Column(String, nullable=True)
    preferred_work_mode = Column(String, default="Hybrid") # Remote, Onsite, Hybrid
    is_deleted = Column(Boolean, default=False, index=True) # GDPR / DPDP Soft-delete

    # Relationships
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skill_items = relationship("CandidateSkillItem", back_populates="candidate", cascade="all, delete-orphan")
    experience_items = relationship("CandidateExperienceItem", back_populates="candidate", cascade="all, delete-orphan")
    education_items = relationship("CandidateEducationItem", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("CandidateScore", back_populates="candidate", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    histories = relationship("CandidateHistory", back_populates="candidate", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="candidate", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="candidate", cascade="all, delete-orphan")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="candidate", cascade="all, delete-orphan")
    sources = relationship("CandidateSource", back_populates="candidate", cascade="all, delete-orphan")
    activities = relationship("CandidateActivity", back_populates="candidate", cascade="all, delete-orphan")
    reference_checks = relationship("ReferenceCheck", back_populates="candidate", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="candidate", cascade="all, delete-orphan")
    comments = relationship("RecruiterComment", back_populates="candidate", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="candidate", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="candidate", cascade="all, delete-orphan")
    consents = relationship("CandidateConsent", back_populates="candidate", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String, default="Applied", nullable=False, index=True) # Applied, Screened, Assessment, Interview, Offer, Hired, Rejected
    match_score = Column(Float, default=0.0)
    rejection_reason = Column(String, nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")


# --- Granular Profile Attributes ---

class CandidateSkillItem(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String, nullable=False, index=True)
    proficiency = Column(String, default="Intermediate") # Beginner, Intermediate, Expert
    years_experience = Column(Float, default=1.0)

    candidate = relationship("Candidate", back_populates="skill_items")


class CandidateExperienceItem(Base):
    __tablename__ = "candidate_experiences"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String, nullable=False)
    role_title = Column(String, nullable=False)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="experience_items")


class CandidateEducationItem(Base):
    __tablename__ = "candidate_educations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_name = Column(String, nullable=False)
    degree_name = Column(String, nullable=False) # B.Tech, M.Tech, MCA, MBA, Ph.D, etc.
    field_of_study = Column(String, nullable=True) # Computer Science, Electrical, etc.
    graduation_year = Column(Integer, nullable=True)
    gpa = Column(String, nullable=True)

    candidate = relationship("Candidate", back_populates="education_items")


# --- Resumes & Embedding Index ---

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # e.g. pdf, txt, docx
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, default={})
    embedding = Column(JSON, nullable=True) # List of floats
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="resumes")


# --- Scoring, Evaluation & Recommendations ---

class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, nullable=False, index=True)
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    experience_gap = Column(Integer, default=0)
    skill_gap_report = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="scores")
    job = relationship("Job", back_populates="scores")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation = Column(String, nullable=False) # e.g. Shortlisted, Under Review, Rejected
    strengths = Column(JSON, default=[])
    weaknesses = Column(JSON, default=[])
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="recommendations")
    job = relationship("Job", back_populates="recommendations")


# --- Interviews, Slots & Structured Feedback ---

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    interviewer_name = Column(String, nullable=False)
    interviewer_email = Column(String, nullable=False)
    scheduled_time = Column(String, nullable=False) # ISO string or datetime representation
    duration_minutes = Column(Integer, default=45)
    mode = Column(String, default="Online") # Online, In-Person, Phone
    meeting_link = Column(String, nullable=True)
    status = Column(String, default="Scheduled", nullable=False, index=True) # Scheduled, Completed, Cancelled, Rescheduled
    notes = Column(Text, nullable=True)
    calendar_event_id = Column(String, nullable=True)
    calendar_invite = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    slots = relationship("InterviewSlot", back_populates="interview", cascade="all, delete-orphan")
    feedbacks = relationship("InterviewFeedback", back_populates="interview", cascade="all, delete-orphan")


class InterviewSlot(Base):
    __tablename__ = "interview_slots"

    id = Column(Integer, primary_key=True, index=True)
    interviewer_name = Column(String, nullable=False)
    interviewer_email = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_booked = Column(Boolean, default=False)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True)

    interview = relationship("Interview", back_populates="slots")


class InterviewFeedback(Base):
    __tablename__ = "interview_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    interviewer_name = Column(String, nullable=False)
    overall_rating = Column(Float, nullable=False) # 1.0 - 5.0
    technical_rating = Column(Float, nullable=True) # 1.0 - 5.0
    communication_rating = Column(Float, nullable=True) # 1.0 - 5.0
    cultural_fit_rating = Column(Float, nullable=True) # 1.0 - 5.0
    recommendation = Column(String, nullable=False) # Strong Hire, Hire, Leaning Hire, Leaning No Hire, No Hire
    notes = Column(Text, nullable=True)
    strengths = Column(JSON, default=[])
    growth_areas = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    interview = relationship("Interview", back_populates="feedbacks")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    category = Column(String, nullable=True) # Technical, Behavioral, Scenario
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="interview_questions")
    job = relationship("Job", back_populates="interview_questions")


# --- Assessments & Sandboxed Code Evaluation ---

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_provider = Column(String, nullable=False)  # HackerRank, Codility, Mettl, Sandbox, Greenhouse
    test_name = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    status = Column(String, default="Pending")  # Pending, Completed, Expired, Failed
    completed_at = Column(DateTime(timezone=True), nullable=True)
    report_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="assessments")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String, default="python") # python, javascript, java, cpp, sql
    code_submission = Column(Text, nullable=True)
    passed_tests = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    execution_time_ms = Column(Float, default=0.0)
    error_output = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("Assessment", back_populates="attempts")
    candidate = relationship("Candidate", back_populates="assessment_attempts")


# --- Sourcing, Journey Tracking & Collaboration ---

class CandidateSource(Base):
    __tablename__ = "candidate_sources"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String, nullable=False)  # LinkedIn, Indeed, Referral, Webhook, Greenhouse, Lever
    source_type = Column(String, nullable=False)  # Job Board, Direct, External API, Referral
    external_candidate_id = Column(String, nullable=True)
    sourcing_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="sources")


class CandidateActivity(Base):
    __tablename__ = "candidate_activities"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = Column(String, nullable=False)  # status_change, comment_added, interview_scheduled, etc.
    description = Column(Text, nullable=False)
    created_by = Column(String, nullable=True)  # System, Username
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="activities")


class CandidateHistory(Base):
    __tablename__ = "candidate_history"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    performed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="histories")


class RecruiterComment(Base):
    __tablename__ = "recruiter_comments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    author = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="comments")


# --- Reference & Background Verification ---

class ReferenceCheck(Base):
    __tablename__ = "reference_checks"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    referee_name = Column(String, nullable=False)
    referee_contact = Column(String, nullable=True)
    referee_relationship = Column(String, nullable=True)  # Manager, Peer, Client
    status = Column(String, default="Pending")  # Pending, Completed, Failed
    comments = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="reference_checks")


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_type = Column(String, nullable=False)  # Background, Education, Employment, Identity
    status = Column(String, default="Pending")  # Pending, Verified, Discrepancy, Failed
    agency = Column(String, nullable=True)  # Checkr, SpringVerify, Internal
    details = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="verifications")


# --- Offers & Compensation Management ---

class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    base_salary = Column(Float, nullable=False)
    bonus = Column(Float, default=0.0)
    stock_grant = Column(Float, default=0.0)
    currency = Column(String, default="INR")  # INR, USD, EUR
    status = Column(String, default="Draft", index=True) # Draft, Sent, Accepted, Rejected, Expired
    offer_letter_text = Column(Text, nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    candidate = relationship("Candidate", back_populates="offers")
    job = relationship("Job", back_populates="offers")


# --- Predictions & AI Analytics ---

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_status = Column(String, nullable=False)  # Selected, Rejected, Interview
    probability = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    model_version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="predictions")


class DailyAnalyticsMetric(Base):
    __tablename__ = "daily_analytics_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_date = Column(String, nullable=False, index=True) # YYYY-MM-DD
    metric_name = Column(String, nullable=False, index=True) # candidates_sourced, interviews_completed, etc.
    metric_value = Column(Float, default=0.0)
    dimensions = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- Platform Integrations & Audit Logging ---

class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, unique=True, nullable=False, index=True) # GoogleCalendar, Outlook, HackerRank, SendGrid, etc.
    provider_category = Column(String, nullable=False) # Calendar, Assessment, Email, ATS, BackgroundCheck
    is_enabled = Column(Boolean, default=False)
    config_data = Column(JSON, default={})
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False, index=True) # LOGIN, CANDIDATE_VIEW, STATUS_UPDATE, OFFER_CREATE, DATA_EXPORT
    resource_type = Column(String, nullable=False, index=True) # Candidate, Job, Offer, User, Integration
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    details = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="audit_logs")


# --- Privacy & Compliance (GDPR / Indian DPDP) ---

class CandidateConsent(Base):
    __tablename__ = "candidate_consents"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String, nullable=False) # resume_processing, background_verification, communication
    granted = Column(Boolean, default=True)
    ip_address = Column(String, nullable=True)
    terms_version = Column(String, default="1.0")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="consents")

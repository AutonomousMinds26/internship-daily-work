from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Recruiter, Hiring Manager, Admin, Candidate
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    location = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    status = Column(String, default="Applied", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Extended database enhancement fields
    ai_summary = Column(Text, nullable=True)
    resume_hash = Column(String, unique=True, index=True, nullable=True)
    ats_score = Column(Float, default=0.0)
    match_score = Column(Float, default=0.0)
    screening_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    ats_details = Column(JSON, nullable=True)


    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("CandidateScore", back_populates="candidate", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    histories = relationship("CandidateHistory", back_populates="candidate", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="candidate", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="candidate", cascade="all, delete-orphan")
    sources = relationship("CandidateSource", back_populates="candidate", cascade="all, delete-orphan")
    activities = relationship("CandidateActivity", back_populates="candidate", cascade="all, delete-orphan")
    reference_checks = relationship("ReferenceCheck", back_populates="candidate", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="candidate", cascade="all, delete-orphan")
    comments = relationship("RecruiterComment", back_populates="candidate", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="candidate", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=[])       # List of required skills
    experience_required = Column(Integer, default=0, index=True) # Years required
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scores = relationship("CandidateScore", back_populates="job", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="job", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="job", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # e.g. pdf, txt, docx
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Extended database enhancement fields
    embedding = Column(JSON, nullable=True) # Stored as JSON list of floats

    candidate = relationship("Candidate", back_populates="resumes")

class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, nullable=False, index=True)
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    experience_gap = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Extended database enhancement fields
    skill_gap_report = Column(JSON, nullable=True)

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Extended database enhancement fields
    calendar_event_id = Column(String, nullable=True)
    calendar_invite = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    slots = relationship("InterviewSlot", back_populates="interview", cascade="all, delete-orphan")

class CandidateHistory(Base):
    __tablename__ = "candidate_history"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String, nullable=False) # e.g. Status Updated, Interview Scheduled, Email Sent
    details = Column(Text, nullable=True)
    performed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="histories")

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


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_provider = Column(String, nullable=False)  # e.g., Greenhouse, Codility, HackerRank, Lever, Mettl
    test_name = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    status = Column(String, default="Pending")  # Pending, Completed, Expired, Failed
    completed_at = Column(DateTime(timezone=True), nullable=True)
    report_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="assessments")


class CandidateSource(Base):
    __tablename__ = "candidate_sources"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String, nullable=False)  # LinkedIn, Indeed, Referral, Webhook, Greenhouse, etc.
    source_type = Column(String, nullable=False)  # Job Board, Direct, External API, etc.
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
    created_by = Column(String, nullable=True)  # System, User
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="activities")


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
    agency = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="verifications")


class RecruiterComment(Base):
    __tablename__ = "recruiter_comments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    author = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="comments")


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

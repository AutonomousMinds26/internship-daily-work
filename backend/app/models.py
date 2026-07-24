from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
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

    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("CandidateScore", back_populates="candidate", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    histories = relationship("CandidateHistory", back_populates="candidate", cascade="all, delete-orphan")

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

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # e.g. pdf, txt, docx
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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

    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")

class CandidateHistory(Base):
    __tablename__ = "candidate_history"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String, nullable=False) # e.g. Status Updated, Interview Scheduled, Email Sent
    details = Column(Text, nullable=True)
    performed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="histories")


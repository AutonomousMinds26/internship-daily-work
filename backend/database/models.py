from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    resume_path = Column(String, nullable=True)
    
    # Score fields
    ats_score = Column(Float, default=0.0)
    match_score = Column(Float, default=0.0)
    screening_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    
    # Status (Applied, Screening, Shortlisted, Interview, Selected, Rejected)
    status = Column(String, default="Applied")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Compatibility fields for legacy verify_foundation.py and matching logic
    skills = Column(String, nullable=True)
    education = Column(String, nullable=True)
    experience = Column(Integer, default=0)
    notice_period = Column(String, nullable=True)
    location = Column(String, nullable=True)
    preferred_location = Column(String, nullable=True)
    expected_CTC = Column(String, nullable=True)
    score = Column(Float, default=0.0)  # Maps legacy score field

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
    job_title = Column(String, nullable=False)
    required_skills = Column(String, nullable=False)
    experience = Column(Integer, default=0)
    location = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    notice_period_requirement = Column(String, nullable=True)


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

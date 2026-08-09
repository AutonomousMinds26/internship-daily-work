from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
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

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=False)
    required_skills = Column(String, nullable=False)
    experience = Column(Integer, default=0)
    location = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    notice_period_requirement = Column(String, nullable=True)

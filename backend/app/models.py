from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Recruiter, Hiring Manager, Admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    education = Column(Text, nullable=True)
    
    experience = Column(Integer, default=0)  # Years of experience
    skills = Column(JSON, default=[])         # List of skills
    projects = Column(JSON, default=[])       # List of projects
    notice_period = Column(String, nullable=True)
    expected_ctc = Column(String, nullable=True)
    location = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    status = Column(String, default="Applied", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=[])       # List of required skills
    experience_required = Column(Integer, default=0) # Years required
    created_at = Column(DateTime(timezone=True), server_default=func.now())

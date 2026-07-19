from sqlalchemy import Column, Integer, String, Float
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    skills = Column(String, nullable=True)  # Store as comma-separated values (e.g. "Python, SQL, AWS")
    education = Column(String, nullable=True)
    experience = Column(Integer, default=0) # In years
    notice_period = Column(String, nullable=True) # e.g. "30 days", "60 days", "90 days"
    location = Column(String, nullable=True) # Current location
    preferred_location = Column(String, nullable=True)
    expected_CTC = Column(String, nullable=True) # Expected CTC
    resume_path = Column(String, nullable=True)
    score = Column(Float, default=0.0)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=False)
    required_skills = Column(String, nullable=False) # Store as comma-separated values
    experience = Column(Integer, default=0) # Required experience in years
    location = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    notice_period_requirement = Column(String, nullable=True)

import pytest
from AI.ats_analyzer import analyze_ats

def test_ats_analyzer_high_match():
    cand = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "phone": "+1234567890",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis"],
        "experience": 5,
        "education": "B.Tech Computer Science",
        "projects": ["Enterprise Microservices", "Real-Time Payment Gateway"],
        "resume_text": "Experienced Python Engineer building FastAPI services on AWS with Docker and PostgreSQL."
    }
    job = {
        "job_title": "Python Backend Engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "experience": 3,
        "description": "Looking for a backend engineer with Python, FastAPI, and Docker skills."
    }

    res = analyze_ats(cand, job)
    assert isinstance(res, dict)
    assert res["ats_score"] >= 75.0
    assert res["recommendation"] in ["ATS Friendly", "Good Match"]
    assert "skill_match" in res
    assert "keyword_match" in res


def test_ats_analyzer_low_match():
    cand = {
        "name": "Sales Person",
        "email": "sales@example.com",
        "skills": ["Direct Sales", "Cold Calling"],
        "experience": 1,
        "resume_text": "Experienced sales executive specializing in B2B customer relationships."
    }
    job = {
        "job_title": "Machine Learning Engineer",
        "required_skills": ["PyTorch", "TensorFlow", "CUDA", "Python"],
        "experience": 5,
        "description": "Deep learning and neural network model training."
    }

    res = analyze_ats(cand, job)
    assert res["ats_score"] < 50.0
    assert len(res.get("issues", [])) > 0


def test_ats_analyzer_empty_resume():
    cand = {"name": "", "email": "", "skills": [], "resume_text": ""}
    job = {"job_title": "Developer", "required_skills": ["Python"]}
    res = analyze_ats(cand, job)
    assert res["ats_score"] <= 40.0

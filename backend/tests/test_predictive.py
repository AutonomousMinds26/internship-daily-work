import pytest
from AI.predictive import predict_hiring_outcome, get_sample_frontend_output

def test_predictive_strong_candidate():
    cand = {
        "name": "Sarah Connor",
        "email": "sarah@example.com",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 6,
        "education": "Master of Science in Computer Science",
        "projects": ["Distributed Task Queue", "Microservice Gateway"],
        "employment_gap": False
    }
    job = {
        "job_title": "Senior Backend Engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 4
    }

    pred = predict_hiring_outcome(cand, job, final_score=88.5)
    assert pred["hiring_probability"] >= 0.80
    assert pred["hiring_probability_category"] == "High"
    assert pred["risk_level"] == "Low"
    assert pred["recommendation"] == "Strong Hire"
    assert len(pred["strengths"]) > 0
    assert "explanation" in pred


def test_predictive_medium_candidate():
    cand = {
        "name": "Alex Rivera",
        "email": "alex@example.com",
        "skills": ["Python", "Flask", "SQL"],
        "experience": 3,
        "education": "Bachelor of Technology",
        "projects": ["Blog App"]
    }
    job = {
        "job_title": "Python Developer",
        "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "experience": 3
    }

    pred = predict_hiring_outcome(cand, job, final_score=68.0)
    assert 0.60 <= pred["hiring_probability"] < 0.80
    assert pred["hiring_probability_category"] == "Medium"
    assert pred["risk_level"] == "Medium"
    assert len(pred["missing_skills"]) > 0


def test_predictive_weak_candidate():
    cand = {
        "name": "Tom Poor",
        "email": "tom@example.com",
        "skills": ["HTML"],
        "experience": 0,
        "education": "High School"
    }
    job = {
        "job_title": "Lead Cloud Architect",
        "required_skills": ["Kubernetes", "AWS", "Terraform", "Go"],
        "experience": 8
    }

    pred = predict_hiring_outcome(cand, job, final_score=35.0)
    assert pred["hiring_probability"] < 0.60
    assert pred["hiring_probability_category"] == "Low"
    assert pred["risk_level"] == "High"
    assert "Reject" in pred["recommendation"]
    assert len(pred["risks"]) > 0


def test_sample_frontend_output():
    samples = get_sample_frontend_output()
    assert isinstance(samples, list)
    assert len(samples) == 3
    categories = [s["hiring_probability_category"] for s in samples]
    assert "High" in categories
    assert "Medium" in categories
    assert "Low" in categories

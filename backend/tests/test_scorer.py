import pytest
from AI.scorer import (
    calculate_enhanced_score,
    calculate_score,
    extract_years,
    normalize
)

def test_extract_years():
    assert extract_years("5 years") == 5
    assert extract_years("3+ yrs of experience") == 3
    assert extract_years(4) == 4
    assert extract_years("10") == 10
    assert extract_years("") == 0
    assert extract_years(None) == 0


def test_normalize():
    assert normalize("  Python  ") == "python"
    assert normalize(None) == ""
    assert normalize(123) == "123"


def test_enhanced_scorer_perfect_candidate():
    candidate = {
        "name": "Sarah Connor",
        "email": "sarah@example.com",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 6,
        "education": "Master of Computer Science",
        "projects": ["Distributed Queue", "API Gateway", "Auth Service"],
        "certifications": ["AWS Solutions Architect"],
        "achievements": ["Hackathon Winner 2024"],
        "languages": ["English", "Spanish"],
        "soft_skills": ["Leadership", "Communication"],
        "expected_ctc": "20 LPA",
        "current_company": "Tech Corp",
        "employment_gap": False
    }
    job = {
        "job_title": "Senior Backend Engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 4,
        "salary_range": "25 LPA"
    }

    res = calculate_enhanced_score(candidate, job)
    assert res["match_percentage"] >= 85.0
    assert res["recommendation"] == "Shortlist"
    assert res["skills_score"] == 30.0
    assert res["experience_score"] == 15.0
    assert len(res["matched_skills"]) == 5
    assert len(res["missing_skills"]) == 0


def test_enhanced_scorer_partial_candidate():
    candidate = {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python"],
        "experience": 2,
        "education": "Bachelor of Technology",
        "projects": ["Simple Blog"],
        "certifications": [],
        "achievements": [],
        "languages": ["English"],
        "soft_skills": [],
        "expected_ctc": "",
        "current_company": "",
        "employment_gap": True
    }
    job = {
        "job_title": "Senior Backend Engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 5
    }

    res = calculate_enhanced_score(candidate, job)
    assert 30.0 <= res["match_percentage"] < 70.0
    assert res["skills_score"] == pytest.approx(6.0, rel=0.1) # 1/5 * 30 = 6
    assert len(res["missing_skills"]) == 4


def test_enhanced_scorer_zero_match():
    candidate = {
        "name": "No Skills",
        "skills": ["Marketing", "Sales"],
        "experience": 0
    }
    job = {
        "required_skills": ["Python", "Docker"]
    }
    res = calculate_enhanced_score(candidate, job)
    assert res["skills_score"] == 0.0
    assert res["match_percentage"] < 50.0
    assert res["recommendation"] == "Reject"

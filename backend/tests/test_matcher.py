import pytest
from AI.ai_matcher import ai_match_candidate

def test_ai_match_candidate_strong_overlap():
    candidate = {
        "name": "David Miller",
        "email": "david@example.com",
        "skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "experience": 4,
        "education": "B.S. in Computer Science"
    }
    job = {
        "job_title": "Python Developer",
        "required_skills": ["Python", "Django", "PostgreSQL"],
        "experience": 3
    }
    res = ai_match_candidate(candidate, job)
    assert isinstance(res, dict)
    assert res["match_percentage"] >= 60.0
    assert "matched_skills" in res
    assert "missing_skills" in res


def test_ai_match_candidate_no_overlap():
    candidate = {
        "name": "Graphic Artist",
        "email": "artist@example.com",
        "skills": ["Photoshop", "Illustrator"],
        "experience": 2
    }
    job = {
        "job_title": "Go / Kubernetes Infrastructure Engineer",
        "required_skills": ["Golang", "Kubernetes", "Terraform"],
        "experience": 4
    }
    res = ai_match_candidate(candidate, job)
    assert res["match_percentage"] < 50.0
    assert len(res["missing_skills"]) >= 2

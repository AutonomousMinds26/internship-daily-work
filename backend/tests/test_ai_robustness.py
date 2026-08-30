import pytest
from AI.screening import generate_questions, evaluate_answers, calculate_final_score
from AI.scorer import calculate_enhanced_score
from AI.ats_analyzer import analyze_ats
from AI.explainability import generate_candidate_explainability
from AI.predictive import predict_hiring_outcome

def test_robustness_missing_skills():
    cand = {"name": "No Skills Cand", "skills": [], "experience": 3}
    job = {"job_title": "Backend Dev", "required_skills": ["Python", "FastAPI", "SQL"]}
    score = calculate_enhanced_score(cand, job)
    assert score["skills_score"] == 0.0
    assert len(score["missing_skills"]) == 3

    expl = generate_candidate_explainability(cand, job)
    assert expl["skill_coverage"] == 0.0
    assert expl["risk_level"] in ["Medium", "High"]


def test_robustness_missing_experience():
    cand = {"name": "Fresh Grad", "skills": ["Python"], "experience": 0}
    job = {"job_title": "Senior Architect", "required_skills": ["Python"], "experience": 10}
    score = calculate_enhanced_score(cand, job)
    assert score["experience_score"] == 0.0

    pred = predict_hiring_outcome(cand, job)
    assert any("deficit" in r.lower() or "experience" in r.lower() for r in pred["risks"])


def test_robustness_empty_resume():
    cand = {"name": "", "email": "", "skills": [], "resume_text": ""}
    job = {"job_title": "Engineer", "required_skills": ["Python"]}
    ats = analyze_ats(cand, job)
    assert ats["ats_score"] <= 40.0


def test_robustness_very_long_resume():
    long_text = "Experienced software engineer. " * 800  # ~25,000 chars
    cand = {
        "name": "Verbose Dev",
        "email": "verbose@example.com",
        "skills": ["Python", "FastAPI"],
        "resume_text": long_text,
        "experience": 5
    }
    job = {"job_title": "Python Dev", "required_skills": ["Python", "FastAPI"]}
    ats = analyze_ats(cand, job)
    assert isinstance(ats["ats_score"], (int, float))
    assert ats["ats_score"] > 0


def test_robustness_candidate_exceeding_requirements():
    cand = {
        "name": "Super Senior",
        "email": "senior@example.com",
        "skills": ["Python", "FastAPI", "Docker", "AWS", "Kubernetes", "Redis", "Kafka", "PostgreSQL"],
        "experience": 12,
        "education": "Ph.D in Computer Science",
        "projects": ["Distributed DB", "Cloud Native Platform", "Kernel Module"],
        "certifications": ["AWS Certified Solutions Architect"],
        "achievements": ["Published author in IEEE"],
        "languages": ["English", "German"],
        "soft_skills": ["Leadership", "Architecture Design"],
        "current_company": "Global Tech Corp",
        "employment_gap": False
    }
    job = {
        "job_title": "Junior Python Dev",
        "required_skills": ["Python"],
        "experience": 1
    }
    score = calculate_enhanced_score(cand, job)
    assert score["match_percentage"] >= 90.0
    assert score["recommendation"] == "Shortlist"

    expl = generate_candidate_explainability(cand, job)
    assert expl["recommendation"] == "Strong Hire"
    assert expl["risk_level"] == "Low"


def test_robustness_explainability_bundle_keys():
    cand = {"name": "Test Cand", "skills": ["Python"], "experience": 3}
    job = {"job_title": "Python Engineer", "required_skills": ["Python"]}
    bundle = generate_candidate_explainability(cand, job)
    
    expected_keys = [
        "ats_score", "match_score", "screening_score", "skill_coverage",
        "experience_fit", "final_score", "hiring_probability", "risk_level",
        "strengths", "weaknesses", "missing_skills", "recommendation", "explanation"
    ]
    for k in expected_keys:
        assert k in bundle, f"Missing explainability key: {k}"

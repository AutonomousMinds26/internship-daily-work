import pytest
from AI.ats_analyzer import analyze_ats_fallback
from AI.screening_questionnaire import generate_screening_questionnaire_fallback
from AI.screening_evaluator import evaluate_answer_fallback, calculate_final_score
from AI.feedback_analyzer import analyze_feedback_fallback

def get_token(client, username, password="password123"):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_ats_analyzer_fallback():
    candidate = {
        "name": "Alex Mercer",
        "email": "alex.mercer@example.com",
        "phone": "+15550199",
        "skills": ["Python", "FastAPI", "SQL"],
        "education": "Master of Science in Software Engineering",
        "projects": ["Project Phoenix (FastAPI inventory)", "Project Aegis (Python scraper)"],
        "resume_text": "Alex Mercer is a Python developer. LinkedIn: linkedin.com/in/alexmercer"
    }
    job = {
        "job_title": "Backend API Developer",
        "required_skills": ["Python", "FastAPI", "Docker"],
        "experience": 3,
        "description": "Looking for a Master's degree holder with strong Python and FastAPI skills."
    }

    result = analyze_ats_fallback(candidate, job)
    assert "ats_score" in result
    assert result["skill_match"] > 0
    assert result["resume_completeness"] == 100
    assert "No LinkedIn profile detected" not in result["issues"]
    assert "No GitHub profile detected" in result["issues"]

def test_screening_questionnaire_fallback():
    candidate = {
        "skills": ["Python", "FastAPI"],
        "experience": 2
    }
    job = {
        "job_title": "Developer",
        "required_skills": ["Python", "SQL"],
        "experience": 3,
        "location": "Pune"
    }

    result = generate_screening_questionnaire_fallback(candidate, job)
    assert "technical_questions" in result
    assert "location_questions" in result
    assert len(result["location_questions"]) > 0
    assert "Pune" in result["location_questions"][0]

def test_screening_evaluator_fallback():
    candidate = {"name": "Bob"}
    
    # Python question
    eval1 = evaluate_answer_fallback(candidate, "How many years of Python experience do you have?", "I have 4 years of Python experience.")
    assert eval1["score"] >= 7
    assert "High" in eval1["relevance"] or "Medium" in eval1["relevance"]
    
    # Location question
    eval2 = evaluate_answer_fallback(candidate, "Are you willing to relocate to Pune?", "No, I cannot relocate to Pune.")
    assert eval2["score"] <= 4
    assert "Low" in eval2["relevance"]
    assert len(eval2["concerns"]) > 0

    # Final composite score calculation
    final = calculate_final_score(screening_score=80.0, ats_score=90.0, match_score=75.0)
    # 0.3*90 + 0.5*75 + 0.2*80 = 27 + 37.5 + 16 = 80.5
    assert final == 80.5

def test_feedback_analyzer_fallback():
    feedbacks = [
        "Candidate has a very strong grasp of Python. 4/5 rating.",
        {"comment": "Excellent communication, but minor concern regarding limited AWS experience.", "rating": 5}
    ]

    result = analyze_feedback_fallback(feedbacks)
    assert "average_rating" in result
    assert result["average_rating"] > 3.0
    assert any("AWS" in s for s in result["concerns"])
    assert any("communication" in s.lower() or "python" in s.lower() for s in result["positive_points"])

def test_api_routes(client):
    token = get_token(client, "recruiter_user")

    # Create Job
    job_res = client.post(
        "/job",
        json={
            "title": "FastAPI Developer",
            "description": "FastAPI, Python backend engineer.",
            "requirements": ["Python", "FastAPI"],
            "experience_required": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # Create Candidate
    cand_res = client.post(
        "/candidate/create",
        json={
            "name": "Jane",
            "email": "jane@example.com",
            "skills": ["Python"],
            "experience": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cand_res.status_code == 201
    cand_id = cand_res.json()["id"]

    # 1. Test POST /ai/screening-questionnaire
    q_res = client.post(
        f"/ai/screening-questionnaire?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert "technical_questions" in q_data
    assert len(q_data["technical_questions"]) > 0

    # 2. Test POST /ai/evaluate-screening-response
    eval_res = client.post(
        "/ai/evaluate-screening-response",
        json={
            "candidate_id": cand_id,
            "question": "How many years of Python experience do you have?",
            "answer": "I have been writing Python code for over 5 years professionally."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "score" in eval_data
    assert "relevance" in eval_data
    assert "final_score" in eval_data

    # Verify score is saved on Candidate in DB
    get_cand = client.get(
        f"/candidate/{cand_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_cand.status_code == 200
    cand_data = get_cand.json()
    assert cand_data["screening_score"] > 0
    assert cand_data["final_score"] > 0

    # 3. Test POST /ai/feedback-analysis (with custom comments list)
    fb_res = client.post(
        "/ai/feedback-analysis",
        json={
            "candidate_id": cand_id,
            "feedbacks": [
                {"comment": "Strong programmer with solid Python logic.", "rating": 4},
                {"comment": "Slightly weak in system design questions.", "rating": 3}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["average_rating"] == 3.5
    assert len(fb_data["positive_points"]) > 0
    assert len(fb_data["concerns"]) > 0

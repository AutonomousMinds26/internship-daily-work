import json
import pytest
from app.models import Candidate, Job, InterviewSlot, Interview, CandidateHistory, InterviewQuestion

def get_token(client, username, password="password123"):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

# --- Helper to create a candidate and job ---
def setup_candidate_and_job(client, token):
    # Create Job
    job_res = client.post(
        "/job",
        json={
            "title": "Backend Developer",
            "description": "Build APIs using Python and FastAPI.",
            "requirements": ["Python", "FastAPI", "SQL"],
            "experience_required": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # Upload Resume
    resume_content = (
        "Alice Smith\n"
        "Email: alice.smith@example.com\n"
        "Skills: Python, SQL\n"
        "Experience: 3 years\n"
        "Education: B.Tech in CSE\n"
        "Location: Pune\n"
    )
    upload_res = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert upload_res.status_code == 201
    candidate_id = upload_res.json()["id"]

    return candidate_id, job_id

# --- 1. AI Pipeline Integration Tests ---
def test_ai_score_endpoint(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    response = client.post(
        f"/ai/score?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "match_score" in data
    assert data["candidate_id"] == cand_id
    assert data["job_id"] == job_id

def test_ai_summary_endpoint(client):
    token = get_token(client, "recruiter_user")
    cand_id, _ = setup_candidate_and_job(client, token)

    response = client.post(
        f"/ai/summary?candidate_id={cand_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "ai_summary" in data
    assert data["candidate_id"] == cand_id
    assert len(data["ai_summary"]) > 0

def test_ai_skill_gap_endpoint(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    response = client.post(
        f"/ai/skill-gap?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "matched_skills" in data
    assert "missing_skills" in data
    assert "recommendations" in data

def test_ai_interview_questions_endpoint(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    response = client.post(
        f"/ai/interview-questions?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) > 0
    for q in data["questions"]:
        assert "question" in q
        assert "expected_answer" in q

def test_ai_recommendation_endpoint(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    response = client.post(
        f"/ai/recommendation?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "recommendation" in data
    assert "strengths" in data
    assert "weaknesses" in data
    assert "justification" in data

def test_ai_semantic_match_endpoint(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    response = client.post(
        f"/ai/semantic-match?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "semantic_score" in data
    assert "matching_highlights" in data

# --- 2. Candidate Journey Tracking Tests ---
def test_candidate_journey_history(client):
    token = get_token(client, "recruiter_user")
    cand_id, _ = setup_candidate_and_job(client, token)

    # Change candidate status
    status_res = client.patch(
        f"/candidate/{cand_id}/status",
        json={"status": "Shortlisted"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status_res.status_code == 200

    # Retrieve history
    history_res = client.get(
        f"/candidates/{cand_id}/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert history_res.status_code == 200
    history_list = history_res.json()
    assert len(history_list) > 0
    actions = [h["action"] for h in history_list]
    assert "Status Updated" in actions

# --- 3. Duplicate Resume Detection Test ---
def test_duplicate_resume_upload(client):
    token = get_token(client, "recruiter_user")
    
    resume_content = (
        "Duplicate Candidate\n"
        "Email: duplicate@example.com\n"
        "Skills: Python\n"
    )

    # 1. Upload first time
    res1 = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 201

    # 2. Upload second time (should be 409 Conflict)
    res2 = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 409

# --- 4. Slot Booking & Scheduling Invite Tests ---
def test_interview_slot_booking_and_invite(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    # 1. Create slot
    slot_res = client.post(
        "/slots",
        json={
            "interviewer_name": "Dave Interviewer",
            "interviewer_email": "dave@example.com",
            "start_time": "2026-08-10T10:00:00+00:00",
            "end_time": "2026-08-10T10:45:00+00:00"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert slot_res.status_code == 201
    slot_id = slot_res.json()["id"]

    # 2. List slots
    list_res = client.get(
        "/slots",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_res.status_code == 200
    slots = list_res.json()
    assert len(slots) > 0
    assert any(s["id"] == slot_id for s in slots)

    # 3. Book slot
    book_res = client.post(
        f"/slots/{slot_id}/book",
        json={
            "candidate_id": cand_id,
            "job_id": job_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert book_res.status_code == 201
    interview_id = book_res.json()["id"]

    # 4. Download ICS invite
    ics_res = client.get(
        f"/interviews/{interview_id}/invite",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ics_res.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_res.text

# --- 5. Recruitment Tools & Analytics Tests ---
def test_recruitment_tools_and_analytics(client):
    token = get_token(client, "recruiter_user")
    cand_id, job_id = setup_candidate_and_job(client, token)

    # Tool 1: Resume Screening
    screen_res = client.post(
        f"/tools/resume-screening?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert screen_res.status_code == 200
    assert "passed_screening" in screen_res.json()

    # Tool 2: Candidate Assessment
    gen_res = client.post(
        f"/tools/candidate-assessment/generate?candidate_id={cand_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert gen_res.status_code == 200
    assert "assessment_questions" in gen_res.json()

    # Evaluate Assessment
    eval_res = client.post(
        "/tools/candidate-assessment/evaluate",
        json={
            "candidate_id": cand_id,
            "job_id": job_id,
            "answers": [
                {"question": "Q1", "answer": "This is a very long descriptive answer to check passing requirements."},
                {"question": "Q2", "answer": "Another long descriptive answer that passes verification constraints."}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["passed"] is True

    # Analytics: Location distribution
    res_loc = client.get("/analytics/location-distribution", headers={"Authorization": f"Bearer {token}"})
    assert res_loc.status_code == 200
    assert "Pune" in res_loc.json()["location_distribution"]

    # Analytics: Experience distribution
    res_exp = client.get("/analytics/experience-distribution", headers={"Authorization": f"Bearer {token}"})
    assert res_exp.status_code == 200
    assert "Entry Level (0-2 yrs)" in res_exp.json()["experience_distribution"]

    # Analytics: Education distribution
    res_edu = client.get("/analytics/education-distribution", headers={"Authorization": f"Bearer {token}"})
    assert res_edu.status_code == 200

    # Analytics: Hiring funnel
    res_funnel = client.get("/analytics/hiring-funnel", headers={"Authorization": f"Bearer {token}"})
    assert res_funnel.status_code == 200

    # Analytics: Diversity
    res_div = client.get("/analytics/diversity-analytics", headers={"Authorization": f"Bearer {token}"})
    assert res_div.status_code == 200

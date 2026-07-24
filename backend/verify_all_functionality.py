import os
import json
import logging
from fastapi.testclient import TestClient

# Make sure we import app after setting up path
from app.main import app
from app.database import engine, Base

def run_verification():
    print("==================================================")
    print("🔍 RECRUITER AI - COMPREHENSIVE E2E VERIFICATION")
    print("==================================================")

    # Re-create fresh database tables for clean verification
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.main import seed_users
    seed_users()


    client = TestClient(app)

    # 1. Login & Token Retrieval
    print("\n1. Testing Auth Login...")
    login_res = client.post("/auth/token", data={"username": "recruiter_user", "password": "password123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Auth Token successfully retrieved.")

    # 2. Monitoring APIs
    print("\n2. Testing Monitoring APIs (/health, /status, /metrics)...")
    health_res = client.get("/health")
    assert health_res.status_code == 200
    print("   ✅ GET /health ->", health_res.json())

    status_res = client.get("/status")
    assert status_res.status_code == 200
    print("   ✅ GET /status ->", status_res.json())

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    print("   ✅ GET /metrics ->", metrics_res.json())

    # 3. Jobs Management
    print("\n3. Testing Job Creation & Retrieval...")
    job_payload = {
        "title": "Senior Python Backend Engineer",
        "description": "Design and scale microservices with FastAPI & PostgreSQL",
        "requirements": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "experience_required": 4
    }
    create_job_res = client.post("/jobs", json=job_payload, headers=headers)
    assert create_job_res.status_code == 201, f"Create job failed: {create_job_res.text}"
    job_id = create_job_res.json()["id"]
    print(f"   ✅ Created Job ID: {job_id}")

    get_job_res = client.get(f"/jobs/{job_id}", headers=headers)
    assert get_job_res.status_code == 200
    assert get_job_res.json()["title"] == "Senior Python Backend Engineer"
    print("   ✅ Job retrieved from DB/Cache successfully.")

    # 4. Candidate CRUD APIs
    print("\n4. Testing Candidate CRUD APIs...")
    cand_payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+19876543210",
        "education": "M.S. Computer Science",
        "experience": 5,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "projects": ["High-throughput API Gateway"],
        "notice_period": "15 days",
        "expected_ctc": "120000 USD",
        "location": "San Francisco",
        "status": "Applied"
    }
    create_cand_res = client.post("/candidates", json=cand_payload, headers=headers)
    assert create_cand_res.status_code == 201, f"Create candidate failed: {create_cand_res.text}"
    cand_id = create_cand_res.json()["id"]
    print(f"   ✅ Created Candidate ID: {cand_id}")

    get_cand_res = client.get(f"/candidates/{cand_id}", headers=headers)
    assert get_cand_res.status_code == 200
    assert get_cand_res.json()["email"] == "jane.doe@example.com"
    print("   ✅ GET /candidates/{id} passed.")

    update_cand_res = client.put(f"/candidates/{cand_id}", json={"location": "Remote", "status": "Matched"}, headers=headers)
    assert update_cand_res.status_code == 200
    assert update_cand_res.json()["location"] == "Remote"
    assert update_cand_res.json()["status"] == "Matched"
    print("   ✅ PUT /candidates/{id} passed.")

    # 5. Candidate Scoring API
    print("\n5. Testing Candidate Scoring API (/score)...")
    score_res = client.get(f"/score?candidate_id={cand_id}&job_id={job_id}", headers=headers)
    assert score_res.status_code == 200
    score_data = score_res.json()
    print(f"   ✅ Calculated Match Score: {score_data['match_score']}% | Matched Skills: {score_data['details']['matched_skills']}")

    # 6. Candidate Status Update API
    print("\n6. Testing Candidate Status API (/candidates/{id}/status)...")
    status_update_res = client.patch(f"/candidates/{cand_id}/status", json={"status": "Shortlisted"}, headers=headers)
    assert status_update_res.status_code == 200
    assert status_update_res.json()["status"] == "Shortlisted"
    print("   ✅ Updated candidate status to Shortlisted.")

    # 7. Interview Scheduling APIs
    print("\n7. Testing Interview Management APIs...")
    interview_payload = {
        "candidate_id": cand_id,
        "job_id": job_id,
        "interviewer_name": "Tech Lead Alex",
        "interviewer_email": "alex.lead@example.com",
        "scheduled_time": "2026-08-05T14:00:00Z",
        "duration_minutes": 60,
        "mode": "Online",
        "meeting_link": "https://meet.example.com/tech-round-1",
        "notes": "System Design Round"
    }
    sch_res = client.post("/interview", json=interview_payload, headers=headers)
    assert sch_res.status_code == 201, f"Schedule interview failed: {sch_res.text}"
    interview_id = sch_res.json()["id"]
    print(f"   ✅ Scheduled Interview ID: {interview_id}")

    # Check candidate status automatically changed to Interview Scheduled
    cand_after_sch = client.get(f"/candidates/{cand_id}", headers=headers).json()
    assert cand_after_sch["status"] == "Interview Scheduled"
    print("   ✅ Candidate status updated to 'Interview Scheduled'.")

    get_interviews_res = client.get(f"/interview?candidate_id={cand_id}", headers=headers)
    assert get_interviews_res.status_code == 200
    assert len(get_interviews_res.json()) >= 1
    print("   ✅ GET /interview retrieved scheduled interview.")

    put_interview_res = client.put(f"/interview/{interview_id}", json={"notes": "Deep dive into DB optimization"}, headers=headers)
    assert put_interview_res.status_code == 200
    assert put_interview_res.json()["notes"] == "Deep dive into DB optimization"
    print("   ✅ PUT /interview/{id} updated notes.")

    # 8. Recruiter Email APIs
    print("\n8. Testing Recruiter Communication Email APIs...")
    shortlist_email_res = client.post("/send-shortlist", json={"candidate_id": cand_id}, headers=headers)
    assert shortlist_email_res.status_code == 200
    assert shortlist_email_res.json()["success"] is True
    print("   ✅ POST /send-shortlist returned success.")

    interview_email_res = client.post("/send-interview", json={"candidate_id": cand_id}, headers=headers)
    assert interview_email_res.status_code == 200
    assert interview_email_res.json()["success"] is True
    print("   ✅ POST /send-interview returned success.")

    rejection_email_res = client.post("/send-rejection", json={"candidate_id": cand_id}, headers=headers)
    assert rejection_email_res.status_code == 200
    assert rejection_email_res.json()["success"] is True
    print("   ✅ POST /send-rejection returned success.")

    # Check candidate status automatically set to Rejected after rejection email
    cand_after_rej = client.get(f"/candidates/{cand_id}", headers=headers).json()
    assert cand_after_rej["status"] == "Rejected"
    print("   ✅ Candidate status updated to 'Rejected' after rejection email.")

    # 9. Verify Rotating Log Files Created
    print("\n9. Verifying Log File Generation...")
    log_files = ["app.log", "error.log", "ai_processing.log"]
    for lf in log_files:
        exists = os.path.exists(lf)
        print(f"   - {lf}: {'EXISTS' if exists else 'NOT FOUND'}")
        assert exists, f"Log file {lf} was not generated."

    # 10. Delete Candidate
    print("\n10. Testing Candidate Deletion...")
    del_cand_res = client.delete(f"/candidates/{cand_id}", headers=headers)
    assert del_cand_res.status_code == 200
    print(f"   ✅ Candidate ID {cand_id} deleted.")

    print("\n==================================================")
    print("🎉 ALL ENDPOINTS & FUNCTIONALITIES VERIFIED 100% WORKING!")
    print("==================================================")

if __name__ == "__main__":
    run_verification()

import os
from fastapi.testclient import TestClient
from database import SessionLocal, Base, engine
import models

# Force create database tables on clean verify db
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

from api import app

client = TestClient(app)

def verify_all():
    print("Starting Foundation Verification...")
    
    # 1. Test GET /
    res_home = client.get("/")
    print("GET / -> Status:", res_home.status_code, "| Body:", res_home.json())
    assert res_home.status_code == 200

    # 2. Create Job: AI Engineer in Pune (Skills: Python, LLM, FastAPI)
    job_payload = {
        "job_title": "AI Engineer",
        "required_skills": "Python, LLM, FastAPI",
        "experience": 2,
        "location": "Pune",
        "salary_range": "12-18 LPA",
        "notice_period_requirement": "30 days"
    }
    res_job = client.post("/jobs", json=job_payload)
    print("POST /jobs -> Status:", res_job.status_code)
    assert res_job.status_code == 201
    job_id = res_job.json()["id"]
    print("Created Job ID:", job_id)

    # 3. Create Candidate: Rahul (Skills: Python, LLM, Git)
    candidate_payload = {
        "name": "Rahul",
        "email": "rahul.dev@example.com",
        "phone": "+919999888877",
        "skills": "Python, LLM, Git",
        "education": "B.Tech",
        "experience": 3,
        "notice_period": "30 days",
        "location": "Mumbai",
        "preferred_location": "Pune",
        "expected_CTC": "15 LPA"
    }
    res_cand = client.post("/candidates", json=candidate_payload)
    print("POST /candidates -> Status:", res_cand.status_code)
    assert res_cand.status_code == 201
    cand_id = res_cand.json()["id"]
    print("Created Candidate ID:", cand_id)

    # 4. Perform Matching and check score update
    # Required skills: Python, LLM, FastAPI (3 skills)
    # Candidate skills: Python, LLM, Git (Matches Python, LLM -> 2/3 = 66.67%)
    # Expected match: 66.67%, Recommendation: "Under Review" (since 66.67 < 70)
    res_match = client.get(f"/match?candidate_id={cand_id}&job_id={job_id}")
    print("GET /match -> Status:", res_match.status_code, "| Result:", res_match.json())
    assert res_match.status_code == 200
    
    match_data = res_match.json()
    assert match_data["candidate_name"] == "Rahul"
    assert match_data["skill_match"] == "66.67%"
    assert match_data["recommendation"] == "Under Review"

    # Verify score is saved in database
    db = SessionLocal()
    updated_cand = db.query(models.Candidate).filter(models.Candidate.id == cand_id).first()
    print("Saved Candidate Score in DB:", updated_cand.score)
    assert updated_cand.score == 66.67
    db.close()

    print("🎉 Verification Successful! Everything is working correctly.")

if __name__ == "__main__":
    verify_all()

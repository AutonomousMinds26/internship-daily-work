import os
from fastapi.testclient import TestClient
from database.database import SessionLocal, Base, engine
import database.models as models
from api import app

# Initialize test database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def verify_pipeline():
    print("Starting Candidate Pipeline Verification...")

    # 1. POST /candidates - Create Candidate
    cand_payload = {
        "name": "Samruddhi Kulkarni",
        "email": "samruddhi@example.com",
        "phone": "+918888777766",
        "skills": "Python, SQL, FastAPI, Machine Learning",
        "education": "Master of Science in Data Science",
        "experience": 3,
        "notice_period": "30 days",
        "location": "Mumbai",
        "preferred_location": "Pune",
        "expected_CTC": "12 LPA"
    }
    res_create = client.post("/candidates", json=cand_payload)
    print("POST /candidates -> Status:", res_create.status_code)
    assert res_create.status_code == 201
    cand_data = res_create.json()
    cand_id = cand_data["id"]
    print("Created Candidate ID:", cand_id)
    assert cand_data["name"] == "Samruddhi Kulkarni"
    assert cand_data["status"] == "Applied"
    assert cand_data["ats_score"] == 0.0
    assert cand_data["final_score"] == 0.0

    # 2. GET /candidates - List Candidates
    res_list = client.get("/candidates")
    print("GET /candidates -> Status:", res_list.status_code, "| Candidates Count:", len(res_list.json()))
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. GET /candidates/{id} - Get Candidate
    res_get = client.get(f"/candidates/{cand_id}")
    print(f"GET /candidates/{cand_id} -> Status:", res_get.status_code)
    assert res_get.status_code == 200
    assert res_get.json()["email"] == "samruddhi@example.com"

    # 4. PUT /candidates/{id} - Update Candidate
    update_payload = {
        "phone": "+918888777777",
        "location": "Pune"
    }
    res_update = client.put(f"/candidates/{cand_id}", json=update_payload)
    print(f"PUT /candidates/{cand_id} -> Status:", res_update.status_code)
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["phone"] == "+918888777777"
    assert updated_data["location"] == "Pune"

    # 5. PUT /candidates/{id}/status - Move through status pipeline
    # Status progression: Applied -> Screening -> Shortlisted -> Interview -> Selected / Rejected
    status_flow = ["Screening", "Shortlisted", "Interview", "Selected"]
    for status_val in status_flow:
        res_status = client.put(f"/candidates/{cand_id}/status", json={"status": status_val})
        print(f"PUT /candidates/{cand_id}/status to '{status_val}' -> Status:", res_status.status_code)
        assert res_status.status_code == 200
        assert res_status.json()["status"] == status_val

    # Test invalid status update (should be 400 Bad Request)
    res_invalid_status = client.put(f"/candidates/{cand_id}/status", json={"status": "InvalidStatus"})
    print("PUT /candidates/{id}/status to 'InvalidStatus' -> Status:", res_invalid_status.status_code)
    assert res_invalid_status.status_code == 400

    # 6. POST /screen-resume - Upload resume, compute ATS, Match, Screening, and Final Scores, save to DB
    # Let's write a mock resume file first
    resume_content = (
        "Alice Smith\n"
        "Email: alice.smith@example.com\n"
        "Phone: +1234567890\n"
        "Skills: Python, SQL, FastAPI, Docker, Git\n"
        "Experience: 3 years of experience\n"
        "Education: Bachelor of Engineering\n"
        "Location: Bangalore\n"
        "Expected CTC: 15 LPA\n"
        "Notice Period: 30 days\n"
    )
    mock_resume_path = "temp_mock_resume.txt"
    with open(mock_resume_path, "w") as f:
        f.write(resume_content)

    try:
        # Create a Job description in DB for matching
        job_payload = {
            "job_title": "FastAPI Architect",
            "required_skills": "Python, SQL, FastAPI, Git",
            "experience": 2,
            "location": "Bangalore",
            "salary_range": "12-18 LPA",
            "notice_period_requirement": "30 days"
        }
        res_job = client.post("/jobs", json=job_payload)
        job_id = res_job.json()["id"]
        print("Created Job for screening ID:", job_id)

        with open(mock_resume_path, "rb") as f:
            res_screen = client.post(
                "/screen-resume",
                files={"file": ("alice_resume.txt", f)},
                data={"job_id": job_id}
            )
        print("POST /screen-resume -> Status:", res_screen.status_code)
        assert res_screen.status_code == 200
        screen_data = res_screen.json()
        assert screen_data["name"] == "Alice Smith"
        assert screen_data["email"] == "alice.smith@example.com"
        print("Extracted scores - ATS:", screen_data["ats_score"],
              "| Match:", screen_data["match_score"],
              "| Screening:", screen_data["screening_score"],
              "| Final:", screen_data["final_score"])
        
        assert screen_data["ats_score"] > 0
        assert screen_data["match_score"] > 0
        assert screen_data["screening_score"] > 0
        assert screen_data["final_score"] > 0
        assert screen_data["status"] == "Applied"

        # Check that Alice is now in the database
        alice_id = screen_data["candidate_id"]
        res_get_alice = client.get(f"/candidates/{alice_id}")
        assert res_get_alice.status_code == 200
        assert res_get_alice.json()["final_score"] == screen_data["final_score"]
        
    finally:
        if os.path.exists(mock_resume_path):
            os.remove(mock_resume_path)

    # 7. GET /reports/summary - Summary Funnel Counts
    res_summary = client.get("/reports/summary")
    print("GET /reports/summary -> Status:", res_summary.status_code, "| Body:", res_summary.json())
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert summary_data["total_candidates"] == 2
    assert summary_data["selected"] == 1  # Samruddhi is Selected
    assert summary_data["applied"] == 1   # Alice is Applied

    # 8. GET /reports/candidates - Candidates Status summary
    res_rep_cand = client.get("/reports/candidates")
    print("GET /reports/candidates -> Status:", res_rep_cand.status_code)
    assert res_rep_cand.status_code == 200
    assert len(res_rep_cand.json()) == 2

    # 9. GET /reports/status - Distribution of statuses
    res_rep_status = client.get("/reports/status")
    print("GET /reports/status -> Status:", res_rep_status.status_code, "| Body:", res_rep_status.json())
    assert res_rep_status.status_code == 200
    assert res_rep_status.json()["status_distribution"]["Selected"] == 1
    assert res_rep_status.json()["status_distribution"]["Applied"] == 1

    # 10. GET /reports/scores - Averages and distribution
    res_rep_scores = client.get("/reports/scores")
    print("GET /reports/scores -> Status:", res_rep_scores.status_code, "| Body:", res_rep_scores.json())
    assert res_rep_scores.status_code == 200
    scores_data = res_rep_scores.json()
    assert scores_data["average_final_score"] > 0
    assert len(scores_data["score_distribution"]) == 2

    # 11. DELETE /candidates/{id} - Delete Candidate
    res_delete = client.delete(f"/candidates/{cand_id}")
    print(f"DELETE /candidates/{cand_id} -> Status:", res_delete.status_code)
    assert res_delete.status_code == 200

    # Verify deleted
    res_get_deleted = client.get(f"/candidates/{cand_id}")
    assert res_get_deleted.status_code == 404

    print("🎉 Pipeline Verification Successful! All endpoints are working exactly as expected.")

if __name__ == "__main__":
    verify_pipeline()

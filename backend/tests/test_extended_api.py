import pytest
from app.models import Candidate, Job, Prediction, RecruiterComment, CandidateActivity, ReferenceCheck, Verification
from app.services.assessment_integration import (
    AssessmentIntegrationManager, APIAuthenticationError,
    APITimeoutError, APIUnavailableError, APIResponseError
)

def get_token(client, username, password="password123"):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


# --- Sourcing APIs Tests ---

def test_source_candidate_success(client):
    token = get_token(client, "recruiter_user")
    
    # 1. Create a job first
    job_res = client.post(
        "/job",
        json={
            "title": "Data Scientist",
            "description": "Python, ML, SQL skills required.",
            "requirements": ["Python", "ML", "SQL"],
            "experience_required": 3
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # 2. Post Sourced candidate
    payload = {
        "candidate": {
            "name": "Jane Sourced",
            "email": "jane.sourced@example.com",
            "phone": "+918888999900",
            "skills": ["Python", "ML"],
            "education": "Master of Science",
            "experience": 4,
            "location": "Mumbai",
            "resume_text": "Experienced data scientist with Python and Machine Learning expertise."
        },
        "source": {
            "source_name": "LinkedIn Sourcing",
            "source_type": "Job Board",
            "external_candidate_id": "li_ext_99812",
            "sourcing_payload": {"campaign": "autumn_recruiting_2026"}
        },
        "job_id": job_id
    }
    
    res = client.post(
        "/sources/candidates",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Jane Sourced"
    assert data["email"] == "jane.sourced@example.com"
    assert data["status"] == "Applied"
    assert data["final_score"] > 0

    # 3. Check duplicate rejection
    res_dup = client.post(
        "/sources/candidates",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_dup.status_code == 409
    assert "Duplicate candidate detected" in res_dup.json()["detail"]


def test_get_sources_stats(client):
    token = get_token(client, "recruiter_user")
    
    # Check stats endpoint
    res = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_bulk_import_candidates(client):
    token = get_token(client, "recruiter_user")
    
    payload = {
        "imports": [
            {
                "candidate": {
                    "name": "Bulk One",
                    "email": "bulk1@example.com",
                    "phone": "9998881111",
                    "skills": ["Python"],
                    "experience": 2
                },
                "source": {
                    "source_name": "Indeed Direct",
                    "source_type": "External API"
                }
            },
            {
                "candidate": {
                    "name": "Bulk Two",
                    "email": "bulk2@example.com",
                    "phone": "9998882222",
                    "skills": ["SQL"],
                    "experience": 1
                },
                "source": {
                    "source_name": "Indeed Direct",
                    "source_type": "External API"
                }
            }
        ]
    }
    
    res = client.post(
        "/candidates/import",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["imported"] == 2
    assert data["duplicates"] == 0
    assert len(data["details"]) == 2


# --- Collaboration APIs Tests ---

def test_collaboration_endpoints(client):
    token = get_token(client, "recruiter_user")
    
    # 1. Setup candidate
    cand_res = client.post(
        "/candidates",
        json={
            "name": "Collaborative Cand",
            "email": "collab@example.com",
            "skills": ["FastAPI"],
            "experience": 3
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    cand_id = cand_res.json()["id"]

    # 2. Add recruiter comment
    comment_res = client.post(
        f"/candidates/{cand_id}/comments",
        json={"comment": "Strong communications skills, FastAPI backend expert."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert comment_res.status_code == 201
    assert comment_res.json()["comment"] == "Strong communications skills, FastAPI backend expert."
    assert comment_res.json()["author"] == "recruiter_user"

    # 3. Get comments list
    get_comments_res = client.get(
        f"/candidates/{cand_id}/comments",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_comments_res.status_code == 200
    assert len(get_comments_res.json()) == 1
    assert get_comments_res.json()[0]["comment"] == "Strong communications skills, FastAPI backend expert."

    # 4. Assign recruiter/status update
    assign_res = client.post(
        f"/candidates/{cand_id}/assign",
        json={"assigned_to": "manager_user", "status": "Screening"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "Screening"

    # 5. Fetch activities
    activity_res = client.get(
        f"/candidates/{cand_id}/activity",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert activity_res.status_code == 200
    activities = activity_res.json()
    assert len(activities) >= 2
    assert any(a["activity_type"] == "comment_added" for a in activities)
    assert any(a["activity_type"] == "candidate_assigned" for a in activities)


# --- Reference & Verification APIs Tests ---

def test_reference_and_verification(client):
    token = get_token(client, "recruiter_user")
    
    # 1. Setup candidate
    cand_res = client.post(
        "/candidates",
        json={
            "name": "Checked Cand",
            "email": "checked@example.com",
            "skills": ["Docker"],
            "experience": 5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    cand_id = cand_res.json()["id"]

    # 2. Reference Check
    ref_res = client.post(
        f"/candidates/{cand_id}/reference-check",
        json={
            "referee_name": "Dr. John Doe",
            "referee_contact": "john.doe@company.com",
            "referee_relationship": "Former Tech Lead",
            "comments": "Highly recommend. Fast learner.",
            "status": "Completed"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ref_res.status_code == 201
    assert ref_res.json()["referee_name"] == "Dr. John Doe"
    assert ref_res.json()["status"] == "Completed"
    assert ref_res.json()["verified_at"] is not None

    ref_list_res = client.get(
        f"/candidates/{cand_id}/reference-check",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ref_list_res.status_code == 200
    assert len(ref_list_res.json()) == 1

    # 3. Background Verification
    verif_res = client.post(
        f"/candidates/{cand_id}/verification",
        json={
            "verification_type": "Education",
            "agency": "GlobalVerify Inc",
            "details": "Verified Master's degree in Computer Science.",
            "status": "Verified"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert verif_res.status_code == 201
    assert verif_res.json()["verification_type"] == "Education"
    assert verif_res.json()["status"] == "Verified"
    assert verif_res.json()["completed_at"] is not None

    verif_list_res = client.get(
        f"/candidates/{cand_id}/verification",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert verif_list_res.status_code == 200
    assert len(verif_list_res.json()) == 1


# --- Predictive Analytics APIs Tests ---

def test_predictive_analytics(client):
    token = get_token(client, "recruiter_user")
    
    # 1. Setup candidate
    cand_res = client.post(
        "/candidates",
        json={
            "name": "Predict Candidate",
            "email": "predict@example.com",
            "skills": ["AWS"],
            "experience": 4
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    cand_id = cand_res.json()["id"]

    # 2. Get Prediction
    pred_res = client.get(
        f"/candidates/{cand_id}/prediction",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert pred_res.status_code == 200
    data = pred_res.json()
    assert "predicted_status" in data
    assert "probability" in data
    assert data["candidate_id"] == cand_id

    # 3. Get Report
    report_res = client.get(
        "/reports/predictions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert report_res.status_code == 200
    r_data = report_res.json()
    assert r_data["total_predictions"] > 0
    assert "predicted_selected_count" in r_data
    assert "average_probability" in r_data


# --- External Assessment Integrations Unit Tests ---

def test_external_assessment_integration_layer():
    # Test Manager
    manager = AssessmentIntegrationManager(use_mock=True)
    
    # HackerRank
    hr_invite = manager.hackerrank.invite_candidate("candidate@example.com", "Python Test")
    assert hr_invite["success"] is True
    assert hr_invite["status"] == "Pending"
    
    hr_res = manager.hackerrank.get_test_results("hr_test_123")
    assert hr_res["status"] == "Completed"
    assert hr_res["score"] == 85.0

    # Codility
    cod_invite = manager.codility.invite_candidate("candidate@example.com", "SQL Test")
    assert cod_invite["success"] is True
    
    cod_res = manager.codility.get_test_results("codility_test_123")
    assert cod_res["score"] == 90.0

    # Mercer Mettl
    mettl_invite = manager.mettl.invite_candidate("candidate@example.com", "Aptitude Test")
    assert mettl_invite["success"] is True
    
    mettl_res = manager.mettl.get_test_results("mettl_test_123")
    assert mettl_res["score"] == 78.0

    # Greenhouse client mock error simulations
    gh = manager.greenhouse
    with pytest.raises(APITimeoutError):
        gh.import_candidate({"email": "timeout@example.com"})
        
    with pytest.raises(APIAuthenticationError):
        gh.import_candidate({"email": "auth_fail@example.com"})
        
    with pytest.raises(APIUnavailableError):
        gh.import_candidate({"email": "unavailable@example.com"})
        
    with pytest.raises(APIResponseError):
        gh.import_candidate({"email": "invalid@example.com"})

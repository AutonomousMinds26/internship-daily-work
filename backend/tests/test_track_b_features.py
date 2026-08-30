import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token
from app.database import SessionLocal
from app.models import Candidate, Job, User
from app.tasks.recruitment_tasks import (
    process_resume_task, bulk_screening_task, send_assessment_task,
    send_notification_email_task, run_background_verification_task,
    aggregate_analytics_daily_task
)
from app.services.assessment_integration import AssessmentIntegrationManager, CodeSandboxClient
from app.services.bias_detector import calculate_adverse_impact_ratio, analyze_diversity_pipeline
from AI.workflow import run_lifecycle_recruitment_graph


@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": "admin_user", "role": "Admin"})


@pytest.fixture
def recruiter_token():
    return create_access_token(data={"sub": "recruiter_user", "role": "Recruiter"})


# ==========================================
# 1. Admin & RBAC Tests
# ==========================================

def test_admin_list_users(client, admin_token, recruiter_token):
    # Recruiter forbidden
    res = client.get("/admin/users", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert res.status_code == 403

    # Admin allowed
    res = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_admin_create_and_update_user(client, admin_token):
    import time
    uname = f"test_user_{int(time.time())}"
    create_res = client.post(
        "/admin/users",
        json={"username": uname, "password": "password123", "role": "Recruiter"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 201
    user_data = create_res.json()
    user_id = user_data["id"]

    # Update role
    update_res = client.put(
        f"/admin/users/{user_id}/role",
        json={"role": "Hiring Manager", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["role"] == "Hiring Manager"


def test_admin_integrations_and_system_status(client, admin_token):
    int_res = client.get("/admin/integrations", headers={"Authorization": f"Bearer {admin_token}"})
    assert int_res.status_code == 200
    assert len(int_res.json()) >= 5

    status_res = client.get("/admin/system-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["status"] in ("Healthy", "Degraded")
    assert "database" in data
    assert "background_worker" in data


def test_admin_audit_logs(client, admin_token):
    res = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ==========================================
# 2. Offer Management Tests
# ==========================================

def test_offer_crud_lifecycle(client, recruiter_token):
    # Ensure a candidate and a job exist
    cand_res = client.get("/candidates", headers={"Authorization": f"Bearer {recruiter_token}"})
    cands = cand_res.json()
    if isinstance(cands, list) and len(cands) > 0:
        cand_id = cands[0]["id"]
    else:
        created_c = client.post(
            "/candidates",
            json={"name": "Offer Test Candidate", "email": "offer.test@example.com", "skills": ["Python"]},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        ).json()
        cand_id = created_c["id"]

    job_res = client.get("/jobs", headers={"Authorization": f"Bearer {recruiter_token}"})
    jbs = job_res.json()
    if isinstance(jbs, list) and len(jbs) > 0:
        job_id = jbs[0]["id"]
    else:
        created_j = client.post(
            "/jobs",
            json={"title": "Offer Engineer", "description": "Job for offer testing", "requirements": ["Python"]},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        ).json()
        job_id = created_j["id"]

    # Create offer
    create_res = client.post(
        "/offers",
        json={
            "candidate_id": cand_id,
            "job_id": job_id,
            "base_salary": 1800000.0,
            "bonus": 200000.0,
            "currency": "INR"
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert create_res.status_code == 201
    offer = create_res.json()
    offer_id = offer["id"]

    # Update offer status to Sent
    update_res = client.put(
        f"/offers/{offer_id}",
        json={"status": "Sent"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Sent"

    # List candidate offers
    list_res = client.get(f"/offers/candidate/{cand_id}", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


# ==========================================
# 3. Privacy, GDPR & Indian DPDP Tests
# ==========================================

def test_privacy_consent_and_dsar_export(client, recruiter_token, admin_token):
    cand_res = client.get("/candidates", headers={"Authorization": f"Bearer {recruiter_token}"})
    cands = cand_res.json()
    if isinstance(cands, list) and len(cands) > 0:
        cand_id = cands[0]["id"]
    else:
        created_c = client.post(
            "/candidates",
            json={"name": "Privacy Candidate", "email": "privacy.test@example.com", "skills": ["Python"]},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        ).json()
        cand_id = created_c["id"]

    # Record consent
    consent_res = client.post(
        "/privacy/consent",
        json={"candidate_id": cand_id, "consent_type": "resume_processing", "granted": True}
    )
    assert consent_res.status_code == 201

    # Export DSAR data
    export_res = client.get(f"/privacy/candidates/{cand_id}/export", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert export_res.status_code == 200
    data = export_res.json()
    assert data["candidate_id"] == cand_id
    assert "profile" in data
    assert "resumes" in data
    assert "consents" in data


# ==========================================
# 4. Celery Background Tasks Tests
# ==========================================

def test_celery_tasks_synchronous_execution(db):
    # Ensure candidate & job exist in test db
    c = db.query(Candidate).first()
    if not c:
        c = Candidate(name="Celery Cand", email="celery@test.com", skills=["Python"])
        db.add(c)
        db.commit()
        db.refresh(c)

    j = db.query(Job).first()
    if not j:
        j = Job(title="Celery Dev", description="Python dev", requirements=["Python"])
        db.add(j)
        db.commit()
        db.refresh(j)

    # 1. process_resume_task
    res = process_resume_task(candidate_id=c.id, raw_text="Senior Python FastAPI Developer with AWS experience", filename="resume.txt")
    assert res["success"] is True

    # 2. bulk_screening_task
    res2 = bulk_screening_task(job_id=j.id, candidate_ids=[c.id])
    assert res2["success"] is True

    # 3. send_assessment_task
    res3 = send_assessment_task(candidate_id=c.id, provider="HackerRank", test_name="Python Core")
    assert res3["success"] is True

    # 4. send_notification_email_task
    res4 = send_notification_email_task(recipient_email="test@example.com", subject="Test Email", body="Hello World")
    assert res4["success"] is True

    # 5. run_background_verification_task
    res5 = run_background_verification_task(candidate_id=c.id, verification_type="Degree Verification")
    assert res5["success"] is True

    # 6. aggregate_analytics_daily_task
    res6 = aggregate_analytics_daily_task("2026-08-30")
    assert res6["success"] is True


# ==========================================
# 5. Sandboxed Code Evaluation Tests
# ==========================================

def test_code_sandbox_evaluation():
    runner = CodeSandboxClient()

    # Python solution
    code = """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""
    test_cases = [
        {"input": "[2, 7, 11, 15], 9", "expected": "[0, 1]"},
        {"input": "[3, 2, 4], 6", "expected": "[1, 2]"}
    ]

    result = runner.execute_code(language="python", code=code, test_cases=test_cases)
    assert result["score"] == 100.0
    assert result["passed_tests"] == 2
    assert result["total_tests"] == 2


# ==========================================
# 6. Bias Detection & 4/5ths Rule Tests
# ==========================================

def test_bias_detection_math():
    # 80% rule: 80% vs 100% -> 0.80 (Compliant)
    comp = calculate_adverse_impact_ratio(
        total_protected=10, selected_protected=8,
        total_majority=10, selected_majority=10
    )
    assert comp["has_adverse_impact"] is False
    assert comp["adverse_impact_ratio"] == 0.8

    # Violation: 50% vs 90% -> 0.556 (< 0.80 -> Adverse Impact)
    viol = calculate_adverse_impact_ratio(
        total_protected=10, selected_protected=5,
        total_majority=10, selected_majority=9
    )
    assert viol["has_adverse_impact"] is True
    assert viol["adverse_impact_ratio"] < 0.80


# ==========================================
# 7. Multi-Stage LangGraph Recruitment Lifecycle
# ==========================================

def test_langgraph_lifecycle_execution():
    cand_data = {
        "id": 1,
        "name": "Arun Varma",
        "email": "arun.varma@example.com",
        "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "experience": 4,
        "education": "B.Tech Computer Science (IIT Bombay)"
    }
    job_data = {
        "id": 1,
        "title": "Senior Backend Engineer",
        "description": "Develop high-scale backend services",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": 3,
        "min_salary": 2500000.0,
        "salary_currency": "INR"
    }

    result = run_lifecycle_recruitment_graph(
        candidate_id=1,
        job_id=1,
        candidate_data=cand_data,
        job_data=job_data,
        assessment_provider="HackerRank"
    )

    assert "audit_trail" in result
    assert len(result["audit_trail"]) >= 4
    assert result.get("ats_score", 0) > 0
    assert result.get("match_score", 0) > 0

import json

def get_token(client, username, password="password123"):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

# --- Authentication Tests ---
def test_login_success(client):
    for user in ["admin_user", "recruiter_user", "manager_user"]:
        token = get_token(client, user)
        assert token is not None

def test_login_failure(client):
    response = client.post(
        "/auth/token",
        data={"username": "recruiter_user", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()

# --- RBAC and Jobs Tests ---
def test_create_job_rbac(client):
    recruiter_token = get_token(client, "recruiter_user")
    manager_token = get_token(client, "manager_user")

    job_data = {
        "title": "Software Engineer",
        "description": "Develop and maintain web services.",
        "requirements": ["Python", "FastAPI", "SQL"],
        "experience_required": 3
    }

    # Hiring Manager should not be able to create a job
    response = client.post(
        "/job",
        json=job_data,
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 403

    # Recruiter should be able to create a job
    response = client.post(
        "/job",
        json=job_data,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Software Engineer"
    assert response.json()["id"] is not None

# --- Resume Upload and Parsing Tests ---
def test_upload_resume_rbac_and_parsing(client, mock_redis):
    recruiter_token = get_token(client, "recruiter_user")
    manager_token = get_token(client, "manager_user")

    resume_content = (
        "Jane Doe\n"
        "Email: jane.doe@example.com\n"
        "Phone: 9876543210\n"
        "Experience: 5 years of experience\n"
        "Skills: Python, FastAPI, Docker, SQL, React\n"
        "Education: Bachelor of Engineering\n"
        "Location: Bangalore\n"
        "Expected CTC: 15 LPA\n"
        "Notice Period: 30 days\n"
    )

    # Hiring Manager cannot upload
    response = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 403

    # Recruiter can upload
    response = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"
    assert data["phone"] == "9876543210"
    assert data["experience"] == 5
    assert "Python" in data["skills"]
    assert "FastAPI" in data["skills"]
    assert "Docker" in data["skills"]
    assert data["location"] == "Bangalore"
    assert data["notice_period"] == "30 days"
    assert data["expected_ctc"] == "15 LPA"

    # Verify cached key exists in mock Redis
    candidate_id = data["id"]
    cache_key = f"candidate:{candidate_id}"
    assert cache_key in mock_redis.store

# --- Candidate Retrieve Cache-Aside Test ---
def test_get_candidate_caching(client, mock_redis):
    recruiter_token = get_token(client, "recruiter_user")
    
    resume_content = (
        "John Smith\n"
        "Email: john.smith@example.com\n"
        "Skills: Java, SQL\n"
        "Experience: 2 years\n"
    )

    # 1. Upload candidate
    upload_res = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    candidate_id = upload_res.json()["id"]
    cache_key = f"candidate:{candidate_id}"
    
    # Clean the cache manually to simulate cold startup lookup
    mock_redis.delete(cache_key)
    assert cache_key not in mock_redis.store

    # 2. Get candidate - should hit database, then populate cache (Cache Miss)
    get_res = client.get(
        f"/candidate?id={candidate_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "John Smith"
    
    # Now it should be cached
    assert cache_key in mock_redis.store
    cached_candidate = json.loads(mock_redis.get(cache_key))
    assert cached_candidate["name"] == "John Smith"

    # 3. Modify cached data directly to verify that subsequent requests read from Cache (Cache Hit)
    cached_candidate["name"] = "John Smith (Cached)"
    mock_redis.setex(cache_key, 3600, json.dumps(cached_candidate))

    get_res_2 = client.get(
        f"/candidate?id={candidate_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert get_res_2.status_code == 200
    assert get_res_2.json()["name"] == "John Smith (Cached)" # Returned from Cache!

# --- Scoring API Tests ---
def test_get_score_calculation(client):
    recruiter_token = get_token(client, "recruiter_user")

    # 1. Create a job
    job_res = client.post(
        "/job",
        json={
            "title": "FastAPI Architect",
            "description": "Build high-throughput APIs",
            "requirements": ["Python", "FastAPI", "SQL", "Docker"],
            "experience_required": 4
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    job_id = job_res.json()["id"]

    # 2. Upload candidate
    resume_content = (
        "Alice Cooper\n"
        "Email: alice@example.com\n"
        "Experience: 2 years\n"
        "Skills: Python, FastAPI, Git\n"
    )
    upload_res = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    candidate_id = upload_res.json()["id"]

    # 3. Calculate score
    # Job reqs: Python, FastAPI, SQL, Docker (4 skills). Required exp: 4.
    # Candidate skills: Python, FastAPI. Experience: 2.
    # Skills match: 2/4 = 50%. Experience match: 2/4 = 50%.
    # Weighted Score: 0.6*50 + 0.4*50 = 50.0.
    score_res = client.get(
        f"/score?candidate_id={candidate_id}&job_id={job_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert score_res.status_code == 200
    data = score_res.json()
    assert data["candidate_id"] == candidate_id
    assert data["job_id"] == job_id
    assert data["match_score"] == 50.0
    assert "Python" in data["details"]["matched_skills"]
    assert "FastAPI" in data["details"]["matched_skills"]
    assert "SQL" in data["details"]["missing_skills"]
    assert "Docker" in data["details"]["missing_skills"]
    assert data["details"]["experience_gap"] == 2

# --- Jobs Retrieve test ---
def test_get_jobs_list(client):
    recruiter_token = get_token(client, "recruiter_user")
    manager_token = get_token(client, "manager_user")

    # Create a job
    create_res = client.post(
        "/job",
        json={
            "title": "Data Scientist",
            "description": "ML solutions",
            "requirements": ["Python", "Pandas"],
            "experience_required": 2
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert create_res.status_code == 201

    # Get jobs list as Recruiter
    get_res = client.get(
        "/job",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert get_res.status_code == 200
    jobs = get_res.json()
    assert len(jobs) >= 1
    assert any(j["title"] == "Data Scientist" for j in jobs)

    # Get jobs list as Hiring Manager
    get_res_manager = client.get(
        "/job",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert get_res_manager.status_code == 200

# --- Candidate Status Update test ---
def test_patch_candidate_status(client, mock_redis):
    recruiter_token = get_token(client, "recruiter_user")
    manager_token = get_token(client, "manager_user")

    # 1. Upload candidate
    resume_content = (
        "Bob Taylor\n"
        "Email: bob.taylor@example.com\n"
        "Skills: Python\n"
        "Experience: 1 year\n"
    )
    upload_res = client.post(
        "/upload_resume",
        files={"file": ("resume.txt", resume_content.encode("utf-8"))},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert upload_res.status_code == 201
    candidate = upload_res.json()
    assert candidate["status"] == "Applied"
    candidate_id = candidate["id"]

    # 2. Update status to Shortlisted as Hiring Manager
    patch_res = client.patch(
        f"/candidate/{candidate_id}/status",
        json={"status": "Shortlisted"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert patch_res.status_code == 200
    updated_candidate = patch_res.json()
    assert updated_candidate["status"] == "Shortlisted"

    # 3. Try setting an invalid status
    patch_invalid = client.patch(
        f"/candidate/{candidate_id}/status",
        json={"status": "InvalidStatus"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert patch_invalid.status_code == 400

    # 4. Check candidate endpoint returns updated status (and verify from cache)
    get_res = client.get(
        f"/candidate?id={candidate_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "Shortlisted"

# --- Candidate CRUD Tests ---
def test_candidate_crud(client):
    token = get_token(client, "recruiter_user")

    # 1. Create candidate via POST /candidates
    candidate_data = {
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "phone": "9998887770",
        "education": "BS Computer Science",
        "experience": 4,
        "skills": ["Python", "Machine Learning", "FastAPI"],
        "location": "Los Angeles",
        "status": "Applied"
    }
    create_res = client.post(
        "/candidates",
        json=candidate_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_res.status_code == 201
    created_cand = create_res.json()
    cand_id = created_cand["id"]
    assert created_cand["name"] == "Sarah Connor"

    # 2. List all candidates via GET /candidates
    list_res = client.get(
        "/candidates",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_res.status_code == 200
    assert any(c["id"] == cand_id for c in list_res.json())

    # 3. Get candidate by ID via GET /candidates/{id}
    get_res = client.get(
        f"/candidates/{cand_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "sarah.connor@example.com"

    # 4. Update candidate via PUT /candidates/{id}
    update_res = client.put(
        f"/candidates/{cand_id}",
        json={"location": "San Francisco", "status": "Matched"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["location"] == "San Francisco"
    assert update_res.json()["status"] == "Matched"

    # 5. Delete candidate via DELETE /candidates/{id}
    delete_res = client.delete(
        f"/candidates/{cand_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_res.status_code == 200

    # Verify candidate is deleted
    get_deleted = client.get(
        f"/candidates/{cand_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_deleted.status_code == 404

# --- Interview Management Tests ---
def test_interview_management(client):
    token = get_token(client, "recruiter_user")

    # Create job & candidate
    job_res = client.post(
        "/jobs",
        json={"title": "DevOps Engineer", "description": "Manage CI/CD", "requirements": ["Docker", "Kubernetes"], "experience_required": 3},
        headers={"Authorization": f"Bearer {token}"}
    )
    job_id = job_res.json()["id"]

    cand_res = client.post(
        "/candidates",
        json={"name": "Alex Murphy", "email": "alex.murphy@example.com", "experience": 3, "skills": ["Docker", "Linux"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    cand_id = cand_res.json()["id"]

    # 1. Schedule Interview
    interview_payload = {
        "candidate_id": cand_id,
        "job_id": job_id,
        "interviewer_name": "Dave Bowman",
        "interviewer_email": "dave@example.com",
        "scheduled_time": "2026-08-01T10:00:00Z",
        "duration_minutes": 60,
        "mode": "Online",
        "meeting_link": "https://meet.example.com/interview-1"
    }
    sch_res = client.post(
        "/interview",
        json=interview_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert sch_res.status_code == 201
    interview_data = sch_res.json()
    interview_id = interview_data["id"]
    assert interview_data["interviewer_name"] == "Dave Bowman"

    # Verify candidate status updated to 'Interview Scheduled'
    cand_get = client.get(f"/candidates/{cand_id}", headers={"Authorization": f"Bearer {token}"})
    assert cand_get.json()["status"] == "Interview Scheduled"

    # 2. Get Interviews
    get_list = client.get("/interview", headers={"Authorization": f"Bearer {token}"})
    assert get_list.status_code == 200
    assert any(i["id"] == interview_id for i in get_list.json())

    # 3. Update Interview
    put_res = client.put(
        f"/interview/{interview_id}",
        json={"notes": "Focus on Kubernetes setup"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert put_res.status_code == 200
    assert put_res.json()["notes"] == "Focus on Kubernetes setup"

    # 4. Cancel/Delete Interview
    del_res = client.delete(f"/interview/{interview_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200

# --- Email Communication Tests ---
def test_email_communication(client):
    token = get_token(client, "recruiter_user")

    cand_res = client.post(
        "/candidates",
        json={"name": "Grace Hopper", "email": "grace.hopper@example.com", "skills": ["COBOL", "Python"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    cand_id = cand_res.json()["id"]

    # 1. Send Shortlist
    short_res = client.post(
        "/send-shortlist",
        json={"candidate_id": cand_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert short_res.status_code == 200
    assert short_res.json()["success"] is True

    # Check status updated to Shortlisted
    cand_check = client.get(f"/candidates/{cand_id}", headers={"Authorization": f"Bearer {token}"})
    assert cand_check.json()["status"] == "Shortlisted"

    # 2. Send Interview Email
    inv_res = client.post(
        "/send-interview",
        json={"candidate_id": cand_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert inv_res.status_code == 200

    # 3. Send Rejection Email
    rej_res = client.post(
        "/send-rejection",
        json={"candidate_id": cand_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert rej_res.status_code == 200

    # Check status updated to Rejected
    cand_check2 = client.get(f"/candidates/{cand_id}", headers={"Authorization": f"Bearer {token}"})
    assert cand_check2.json()["status"] == "Rejected"

# --- Monitoring APIs Tests ---
def test_monitoring_endpoints(client):
    # Health check does not require auth
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert "database" in health_res.json()

    # System status
    status_res = client.get("/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "running"

    # Metrics
    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    assert "candidates_by_status" in metrics_res.json()



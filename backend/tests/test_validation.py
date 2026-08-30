import pytest

def get_token(client, username):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": "password123"}
    )
    return response.json()["access_token"]

def test_candidate_name_validation(client):
    token = get_token(client, "admin_user")
    
    # Test short name (under 2 chars)
    resp = client.post(
        "/candidates",
        json={"name": "A", "email": "a@example.com", "skills": ["Python"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422
    
    # Test numbers in name
    resp2 = client.post(
        "/candidates",
        json={"name": "John123", "email": "a@example.com", "skills": ["Python"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 422

def test_candidate_phone_validation(client):
    token = get_token(client, "admin_user")
    
    # Invalid phone format
    resp = client.post(
        "/candidates",
        json={"name": "John Doe", "email": "a@example.com", "phone": "123", "skills": ["Python"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422

def test_candidate_experience_validation(client):
    token = get_token(client, "admin_user")
    
    # Negative experience
    resp = client.post(
        "/candidates",
        json={"name": "John Doe", "email": "a@example.com", "experience": -5, "skills": ["Python"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422

def test_job_validation(client):
    token = get_token(client, "admin_user")
    
    # Empty requirements list
    resp = client.post(
        "/jobs",
        json={"title": "Data Scientist", "description": "High throughput engineering.", "requirements": [], "experience_required": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422
    
    # Short description
    resp2 = client.post(
        "/jobs",
        json={"title": "Data Scientist", "description": "Eng", "requirements": ["Python"], "experience_required": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 422

import pytest

def get_token(client, username):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": "password123"}
    )
    return response.json()["access_token"]

def test_candidates_pagination(client):
    token = get_token(client, "admin_user")
    
    # Create 5 candidates
    names = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]
    for i, name in enumerate(names):
        client.post(
            "/candidates",
            json={
                "name": f"Candidate {name}",
                "email": f"candidate{i}@example.com",
                "skills": ["Python"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
    # Get with limit=2, skip=0
    resp_1 = client.get(
        "/candidates?limit=2&skip=0",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_1.status_code == 200
    candidates_1 = resp_1.json()
    assert len(candidates_1) == 2
    
    # Get with limit=2, skip=2
    resp_2 = client.get(
        "/candidates?limit=2&skip=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_2.status_code == 200
    candidates_2 = resp_2.json()
    assert len(candidates_2) == 2
    
    # Ensure paginated results do not overlap
    cand_1_names = {c["name"] for c in candidates_1}
    cand_2_names = {c["name"] for c in candidates_2}
    assert len(cand_1_names.intersection(cand_2_names)) == 0

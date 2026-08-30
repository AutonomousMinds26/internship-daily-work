import pytest
import time
from jose import jwt
from app.config import settings

def get_token(client, username):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": "password123"}
    )
    return response.json()["access_token"]

def test_expired_token_handling(client):
    # Create an expired token manually
    expire = time.time() - 3600
    to_encode = {"sub": "admin_user", "role": "Admin", "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    # Make request with expired token
    response = client.get(
        "/candidates",
        headers={"Authorization": f"Bearer {encoded_jwt}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"

def test_invalid_token_handling(client):
    # Make request with gibberish token
    response = client.get(
        "/candidates",
        headers={"Authorization": "Bearer not-a-valid-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

def test_logout_token_blacklisting(client, mock_redis):
    token = get_token(client, "admin_user")
    
    # Confirm it works
    resp_check = client.get(
        "/candidates",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_check.status_code == 200
    
    # Log out
    logout_resp = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["detail"] == "Successfully logged out"
    
    # Verify access is now blocked
    blocked_resp = client.get(
        "/candidates",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert blocked_resp.status_code == 401
    assert "blacklisted" in blocked_resp.json()["detail"].lower()

import json


def test_register_success(client):
    """Test standard user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newcandidate",
            "email": "candidate@example.com",
            "password": "Password123",
            "full_name": "Jane Candidate",
            "target_role": "Backend Engineer"
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["username"] == "newcandidate"
    assert data["user"]["email"] == "candidate@example.com"


def test_register_duplicate_username(client, test_user):
    """Test duplicate username registration rejection."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 409
    data = response.get_json()
    assert data["success"] is False
    assert "already taken" in data["error"].lower()


def test_register_invalid_email(client):
    """Test registration validation with malformed email."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "validuser",
            "email": "not-an-email",
            "password": "Password123"
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "valid email" in data["error"].lower()


def test_login_success(client, test_user):
    """Test successful login with correct credentials."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Secret123!"
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["username"] == "testuser"


def test_login_invalid_password(client, test_user):
    """Test login rejection on wrong password."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword999"
        }
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False


def test_get_current_user_profile(client, auth_headers):
    """Test retrieving current user profile with valid JWT."""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["username"] == "testuser"


def test_unauthenticated_request_fails(client):
    """Test protected route rejection without token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False

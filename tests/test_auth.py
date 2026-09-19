from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

from app.models.user import User, RefreshToken


# Create database tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test User",
            "email": "testuser@example.com",
            "password": "Test@12345",
            "role": "Attendee"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test User"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "Attendee"
    assert data["is_active"] is True


def test_duplicate_registration():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Duplicate User",
            "email": "testuser@example.com",
            "password": "Test@12345",
            "role": "Attendee"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login():
    response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Test@12345"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login():
    response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401


def test_get_current_user():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Test@12345"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "testuser@example.com"
    assert data["role"] == "Attendee"


def test_invalid_token():
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        }
    )

    assert response.status_code == 401


def test_refresh_token():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Test@12345"
        }
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_old_refresh_token_cannot_be_reused():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Test@12345"
        }
    )

    assert login_response.status_code == 200

    old_refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token
        }
    )

    assert first_refresh.status_code == 200

    second_refresh = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token
        }
    )

    assert second_refresh.status_code == 401
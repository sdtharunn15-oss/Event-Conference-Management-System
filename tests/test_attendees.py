import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str = "attendee") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


def register_attendee(
    client: TestClient,
    email: str | None = None,
):
    email = email or unique_email()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Attendee",
            "email": email,
            "password": "Password123!",
            "role": "Attendee",
        },
    )

    assert response.status_code == 201

    return response.json()


def login_attendee(
    client: TestClient,
    email: str,
):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    return response.json()


def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_attendee_profile(client: TestClient):

    email = unique_email()

    register_attendee(
        client,
        email,
    )

    tokens = login_attendee(
        client,
        email,
    )

    response = client.post(
        "/attendees",
        headers=auth_headers(
            tokens["access_token"]
        ),
        json={
            "full_name": "Test Attendee",
            "email": email,
            "phone": "9876543210",
            "organization": "Test Organization",
            "designation": "Developer",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Attendee"
    assert data["email"] == email
    assert data["phone"] == "9876543210"
    assert data["organization"] == "Test Organization"
    assert data["designation"] == "Developer"


def test_get_my_attendee_profile(client: TestClient):

    email = unique_email()

    register_attendee(
        client,
        email,
    )

    tokens = login_attendee(
        client,
        email,
    )

    headers = auth_headers(
        tokens["access_token"]
    )

    create_response = client.post(
        "/attendees",
        headers=headers,
        json={
            "full_name": "My Attendee",
            "email": email,
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/attendees/me",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == email
    assert data["full_name"] == "My Attendee"


def test_get_attendee_by_id(client: TestClient):

    email = unique_email()

    register_attendee(
        client,
        email,
    )

    tokens = login_attendee(
        client,
        email,
    )

    headers = auth_headers(
        tokens["access_token"]
    )

    create_response = client.post(
        "/attendees",
        headers=headers,
        json={
            "full_name": "Profile Attendee",
            "email": email,
        },
    )

    assert create_response.status_code == 201

    attendee_id = create_response.json()["id"]

    response = client.get(
        f"/attendees/{attendee_id}",
        headers=headers,
    )

    assert response.status_code == 200

    assert response.json()["id"] == attendee_id


def test_update_my_attendee_profile(client: TestClient):

    email = unique_email()

    register_attendee(
        client,
        email,
    )

    tokens = login_attendee(
        client,
        email,
    )

    headers = auth_headers(
        tokens["access_token"]
    )

    create_response = client.post(
        "/attendees",
        headers=headers,
        json={
            "full_name": "Old Name",
            "email": email,
        },
    )

    assert create_response.status_code == 201

    response = client.put(
        "/attendees/me",
        headers=headers,
        json={
            "full_name": "Updated Name",
            "phone": "9876543210",
            "organization": "Updated Organization",
            "designation": "Manager",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "9876543210"
    assert data["organization"] == "Updated Organization"
    assert data["designation"] == "Manager"


def test_duplicate_attendee_profile(client: TestClient):

    email = unique_email()

    register_attendee(
        client,
        email,
    )

    tokens = login_attendee(
        client,
        email,
    )

    headers = auth_headers(
        tokens["access_token"]
    )

    payload = {
        "full_name": "Test Attendee",
        "email": email,
    }

    first = client.post(
        "/attendees",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/attendees",
        headers=headers,
        json=payload,
    )

    assert second.status_code == 400


def test_attendee_profile_requires_authentication(
    client: TestClient,
):

    response = client.get(
        "/attendees/me"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_non_attendee_cannot_create_profile(
    client: TestClient,
):

    email = unique_email(
        "organizer"
    )

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Organizer",
            "email": email,
            "password": "Password123!",
            "role": "Event Organizer",
        },
    )

    assert response.status_code == 201

    tokens = login_attendee(
        client,
        email,
    )

    response = client.post(
        "/attendees",
        headers=auth_headers(
            tokens["access_token"]
        ),
        json={
            "full_name": "Wrong Role",
            "email": email,
        },
    )

    assert response.status_code == 403
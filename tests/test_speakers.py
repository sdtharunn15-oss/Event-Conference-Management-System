from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_organizer():
    unique_id = uuid4().hex[:8]

    email = f"organizer_{unique_id}@test.com"
    password = "Organizer@12345"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Event Organizer",
            "email": email,
            "password": password,
            "role": "Event Organizer",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_test_speaker():

    token = get_organizer()

    unique_email = (
        f"speaker_{uuid4().hex[:8]}@test.com"
    )

    response = client.post(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Arun Kumar",
            "email": unique_email,
            "phone": "9876543210",
            "bio": "Technology speaker",
            "expertise": "Artificial Intelligence",
            "company": "Tech Company",
            "experience": 10,
        },
    )

    assert response.status_code == 201

    return response.json(), token


def test_create_speaker():

    speaker, token = create_test_speaker()

    assert speaker["name"] == "Arun Kumar"
    assert speaker["expertise"] == "Artificial Intelligence"
    assert speaker["experience"] == 10
    assert speaker["is_active"] is True


def test_get_speakers():

    speaker, token = create_test_speaker()

    response = client.get(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_speaker():

    speaker, token = create_test_speaker()

    speaker_id = speaker["id"]

    response = client.get(
        f"/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == speaker_id
    assert response.json()["name"] == "Arun Kumar"


def test_update_speaker():

    speaker, token = create_test_speaker()

    speaker_id = speaker["id"]

    response = client.put(
        f"/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Arun Kumar Updated",
            "experience": 15,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Arun Kumar Updated"
    assert response.json()["experience"] == 15


def test_duplicate_speaker_email():

    token = get_organizer()

    email = (
        f"duplicate_{uuid4().hex[:8]}@test.com"
    )

    payload = {
        "name": "Duplicate Speaker",
        "email": email,
        "phone": "9876543210",
        "bio": "Test speaker",
        "expertise": "Technology",
        "company": "Test Company",
        "experience": 5,
    }

    first_response = client.post(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Speaker email already registered"
    )


def test_invalid_speaker_experience():

    token = get_organizer()

    response = client.post(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Invalid Speaker",
            "email": f"invalid_{uuid4().hex[:8]}@test.com",
            "phone": "9876543210",
            "bio": "Invalid experience test",
            "expertise": "Technology",
            "company": "Test Company",
            "experience": -1,
        },
    )

    assert response.status_code == 422


def test_get_nonexistent_speaker():

    token = get_organizer()

    response = client.get(
        "/speakers/99999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404
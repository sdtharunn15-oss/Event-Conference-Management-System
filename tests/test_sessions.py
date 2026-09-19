from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def create_user(role: str):
    unique_id = uuid4().hex[:8]

    email = f"{role.lower().replace(' ', '_')}_{unique_id}@test.com"
    password = "Test@12345"

    response = client.post(
        "/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_organizer():
    return create_user("Event Organizer")


def create_speaker(token):
    email = f"speaker_{uuid4().hex[:8]}@test.com"

    response = client.post(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Session Speaker",
            "email": email,
            "phone": "9876543210",
            "bio": "Technology speaker",
            "expertise": "Python",
            "company": "Tech Company",
            "experience": 10,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_venue(token):
    response = client.post(
        "/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "venue_name": f"Session Venue {uuid4().hex[:6]}",
            "address": "Chennai",
            "city": "Chennai",
            "capacity": 500,
            "facilities": "AC, Projector, WiFi",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_hall(token, venue_id):
    response = client.post(
        f"/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "hall_name": f"Main Hall {uuid4().hex[:6]}",
            "capacity": 200,
            "floor": 1,
            "availability_status": "Available",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_event(token):
    start = datetime.now().replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=30)

    end = start + timedelta(hours=8)

    registration_start = start - timedelta(days=10)
    registration_end = start - timedelta(days=1)

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": f"Tech Conference {uuid4().hex[:6]}",
            "description": "Technology conference",
            "event_type": "Conference",
            "organizer_id": get_user_id(token),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "registration_start": registration_start.isoformat(),
            "registration_end": registration_end.isoformat(),
            "capacity": 500,
        },
    )

    assert response.status_code == 201

    return response.json(), start, end


def get_user_id(token):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_session_resources():

    token = create_organizer()

    speaker = create_speaker(token)

    venue = create_venue(token)

    hall = create_hall(
        token,
        venue["id"],
    )

    event, start, end = create_event(token)

    return {
        "token": token,
        "speaker": speaker,
        "venue": venue,
        "hall": hall,
        "event": event,
        "start": start,
        "end": end,
    }


def create_session_payload(resources, start_offset=1):

    start_time = (
        resources["start"]
        + timedelta(hours=start_offset)
    )

    end_time = start_time + timedelta(hours=1)

    return {
        "event_id": resources["event"]["id"],
        "speaker_id": resources["speaker"]["id"],
        "hall_id": resources["hall"]["id"],
        "title": "Introduction to Python",
        "description": "Python session",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "capacity": 100,
        "session_type": "Workshop",
    }


def test_create_session():

    resources = create_session_resources()

    response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=create_session_payload(resources),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["event_id"] == resources["event"]["id"]
    assert data["speaker_id"] == resources["speaker"]["id"]
    assert data["hall_id"] == resources["hall"]["id"]
    assert data["title"] == "Introduction to Python"
    assert data["capacity"] == 100


def test_get_event_sessions():

    resources = create_session_resources()

    payload = create_session_payload(resources)

    create_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/sessions/event/{resources['event']['id']}",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_get_session():

    resources = create_session_resources()

    create_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=create_session_payload(resources),
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.get(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == session_id


def test_update_session():

    resources = create_session_resources()

    create_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=create_session_payload(resources),
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.put(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json={
            "title": "Advanced Python",
            "capacity": 120,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Advanced Python"
    assert response.json()["capacity"] == 120


def test_delete_session():

    resources = create_session_resources()

    create_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=create_session_payload(resources),
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.delete(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
    )

    assert get_response.status_code == 404


def test_session_end_before_start():

    resources = create_session_resources()

    payload = create_session_payload(resources)

    start_time = (
        resources["start"]
        + timedelta(hours=3)
    )

    payload["start_time"] = start_time.isoformat()
    payload["end_time"] = (
        start_time - timedelta(minutes=30)
    ).isoformat()

    response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_session_outside_event_timing():

    resources = create_session_resources()

    payload = create_session_payload(resources)

    payload["start_time"] = (
        resources["end"] + timedelta(hours=1)
    ).isoformat()

    payload["end_time"] = (
        resources["end"] + timedelta(hours=2)
    ).isoformat()

    response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Session must be within event timing"
    )


def test_session_capacity_cannot_exceed_hall():

    resources = create_session_resources()

    payload = create_session_payload(resources)

    payload["capacity"] = 250

    response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Session capacity cannot exceed hall capacity"
    )


def test_hall_overlap_prevented():

    resources = create_session_resources()

    payload = create_session_payload(resources)

    first_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert first_response.status_code == 201

    second_payload = create_session_payload(
        resources,
        start_offset=1,
    )

    second_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=second_payload,
    )

    assert second_response.status_code == 400
    assert (
        second_response.json()["detail"]
        == "Hall already has an overlapping session"
    )


def test_speaker_overlap_prevented():

    resources = create_session_resources()

    payload = create_session_payload(resources)

    first_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert first_response.status_code == 201

    second_hall = create_hall(
        resources["token"],
        resources["venue"]["id"],
    )

    second_payload = create_session_payload(
        resources,
        start_offset=1,
    )

    second_payload["hall_id"] = second_hall["id"]

    second_response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=second_payload,
    )

    assert second_response.status_code == 400
    assert (
        second_response.json()["detail"]
        == "Speaker already has an overlapping session"
    )


def test_inactive_speaker_cannot_be_assigned():

    resources = create_session_resources()

    speaker_id = resources["speaker"]["id"]

    update_response = client.put(
        f"/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json={
            "is_active": False
        },
    )

    assert update_response.status_code == 200

    payload = create_session_payload(resources)

    response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {resources['token']}"
        },
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Inactive speaker cannot be assigned"
    )


def test_nonexistent_event():

    token = create_organizer()

    response = client.post(
        "/sessions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_id": 999999,
            "speaker_id": 999999,
            "hall_id": 999999,
            "title": "Test Session",
            "description": "Test",
            "start_time": (
                datetime.now() + timedelta(days=1)
            ).isoformat(),
            "end_time": (
                datetime.now() + timedelta(days=1, hours=1)
            ).isoformat(),
            "capacity": 50,
            "session_type": "Workshop",
        },
    )

    assert response.status_code == 404


def test_nonexistent_session():

    token = create_organizer()

    response = client.get(
        "/sessions/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404
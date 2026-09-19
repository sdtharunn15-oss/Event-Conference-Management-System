from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def create_user(role: str):
    unique_id = uuid4().hex[:8]

    email = (
        f"{role.lower().replace(' ', '_')}_{unique_id}"
        "@test.com"
    )
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


def create_attendee():
    return create_user("Attendee")


def get_user_id(token):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_speaker(token):
    response = client.post(
        "/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Feedback Speaker",
            "email": f"speaker_{uuid4().hex[:8]}@test.com",
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
            "venue_name": f"Feedback Venue {uuid4().hex[:6]}",
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
            "hall_name": f"Feedback Hall {uuid4().hex[:6]}",
            "capacity": 200,
            "floor": 1,
            "availability_status": "Available",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_event(token):
    now = datetime.now()

    start = now + timedelta(days=30)

    start = start.replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = start + timedelta(hours=8)

    # Registration must currently be open
    registration_start = now - timedelta(days=1)
    registration_end = now + timedelta(days=20)

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": (
                f"Feedback Conference "
                f"{uuid4().hex[:6]}"
            ),
            "description": "Feedback test conference",
            "event_type": "Conference",
            "organizer_id": get_user_id(token),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "registration_start": (
                registration_start.isoformat()
            ),
            "registration_end": (
                registration_end.isoformat()
            ),
            "capacity": 500,
        },
    )

    assert response.status_code == 201, response.text

    return response.json(), start, end
def create_registration(
    attendee_token,
    event_id,
):
    response = client.post(
        f"/events/{event_id}/register",
        headers={
            "Authorization": (
                f"Bearer {attendee_token}"
            )
        },
    )

    assert response.status_code == 201

    return response.json()


def check_in(registration_id):
    response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "Manual"
        },
    )

    assert response.status_code == 201

    return response.json()


def create_feedback_resources():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    speaker = create_speaker(
        organizer_token
    )

    venue = create_venue(
        organizer_token
    )

    create_hall(
        organizer_token,
        venue["id"],
    )

    event, start, end = create_event(
        organizer_token
    )

    registration = create_registration(
        attendee_token,
        event["id"],
    )

    check_in(
        registration["id"]
    )

    return {
        "organizer_token": organizer_token,
        "attendee_token": attendee_token,
        "speaker": speaker,
        "event": event,
        "registration": registration,
        "start": start,
        "end": end,
    }


def test_create_speaker_feedback():

    resources = create_feedback_resources()

    response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": resources["event"]["id"],
            "speaker_id": resources["speaker"]["id"],
            "rating": 5,
            "feedback": "Excellent speaker",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["registration_id"] == (
        resources["registration"]["id"]
    )
    assert data["event_id"] == resources["event"]["id"]
    assert data["speaker_id"] == resources["speaker"]["id"]
    assert data["session_id"] is None
    assert data["rating"] == 5
    assert data["feedback"] == "Excellent speaker"


def test_feedback_requires_speaker_or_session():

    resources = create_feedback_resources()

    response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": resources["event"]["id"],
            "rating": 5,
            "feedback": "Good event",
        },
    )

    assert response.status_code == 422


def test_invalid_rating():

    resources = create_feedback_resources()

    response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": resources["event"]["id"],
            "speaker_id": resources["speaker"]["id"],
            "rating": 6,
            "feedback": "Invalid rating",
        },
    )

    assert response.status_code == 422


def test_feedback_requires_checkin():

    organizer_token = create_organizer()
    attendee_token = create_attendee()

    speaker = create_speaker(
        organizer_token
    )

    event, _, _ = create_event(
        organizer_token
    )

    registration = create_registration(
        attendee_token,
        event["id"],
    )

    response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {attendee_token}"
            )
        },
        json={
            "registration_id": registration["id"],
            "event_id": event["id"],
            "speaker_id": speaker["id"],
            "rating": 5,
            "feedback": "Should fail",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Only attendees who checked in can provide feedback"
    )


def test_feedback_wrong_event():

    resources = create_feedback_resources()

    other_event, _, _ = create_event(
        resources["organizer_token"]
    )

    response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": other_event["id"],
            "speaker_id": resources["speaker"]["id"],
            "rating": 5,
            "feedback": "Wrong event",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Registration does not belong to this event"
    )


def test_feedback_forbidden_for_other_attendee():

    resources = create_feedback_resources()

    another_attendee = create_attendee()

    response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {another_attendee}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": resources["event"]["id"],
            "speaker_id": resources["speaker"]["id"],
            "rating": 5,
            "feedback": "Unauthorized feedback",
        },
    )

    assert response.status_code == 403


def test_duplicate_speaker_feedback():

    resources = create_feedback_resources()

    payload = {
        "registration_id": (
            resources["registration"]["id"]
        ),
        "event_id": resources["event"]["id"],
        "speaker_id": resources["speaker"]["id"],
        "rating": 5,
        "feedback": "Excellent",
    }

    first_response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json=payload,
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Feedback already submitted for this speaker"
    )


def test_nonexistent_event_feedback():

    token = create_attendee()

    response = client.get(
        "/feedback/event/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_nonexistent_speaker_ratings():

    token = create_attendee()

    response = client.get(
        "/feedback/speaker/999999/ratings",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_get_event_feedback():

    resources = create_feedback_resources()

    create_response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": resources["event"]["id"],
            "speaker_id": resources["speaker"]["id"],
            "rating": 4,
            "feedback": "Very good",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/feedback/event/{resources['event']['id']}",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event_id"] == resources["event"]["id"]


def test_get_speaker_ratings():

    resources = create_feedback_resources()

    create_response = client.post(
        "/feedback",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
        json={
            "registration_id": (
                resources["registration"]["id"]
            ),
            "event_id": resources["event"]["id"],
            "speaker_id": resources["speaker"]["id"],
            "rating": 5,
            "feedback": "Excellent",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/feedback/speaker/"
        f"{resources['speaker']['id']}/ratings",
        headers={
            "Authorization": (
                f"Bearer {resources['attendee_token']}"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["speaker_id"] == (
        resources["speaker"]["id"]
    )
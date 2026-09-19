
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def create_user(role: str):
    unique_id = uuid4().hex[:8]

    email = (
        f"{role.lower().replace(' ', '_')}_"
        f"{unique_id}@test.com"
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


def create_event(token):
    start = datetime.now().replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=30)

    end = start + timedelta(hours=8)

    # Registration is already open when the test runs.
    registration_start = datetime.now() - timedelta(days=1)
    registration_end = datetime.now() + timedelta(days=20)

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": (
                f"Check-In Event "
                f"{uuid4().hex[:6]}"
            ),
            "description": "Check-in test event",
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

    assert response.status_code == 201

    return response.json()


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


def create_resources():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(
        organizer_token
    )

    registration = create_registration(
        attendee_token,
        event["id"],
    )

    return {
        "organizer_token": organizer_token,
        "attendee_token": attendee_token,
        "event": event,
        "registration": registration,
    }


def test_check_in_confirmed_registration():

    resources = create_resources()

    registration_id = resources["registration"]["id"]

    response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "Manual"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["registration_id"] == registration_id
    assert data["check_in_method"] == "Manual"
    assert data["check_in_time"] is not None
    assert data["check_out_time"] is None


def test_duplicate_check_in():

    resources = create_resources()

    registration_id = resources["registration"]["id"]

    first_response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "QR Code"
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "QR Code"
        },
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Attendee has already checked in"
    )


def test_check_in_invalid_registration():

    response = client.post(
        "/registrations/999999/check-in",
        json={
            "check_in_method": "Manual"
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Registration not found"
    )


def test_check_out_after_check_in():

    resources = create_resources()

    registration_id = resources["registration"]["id"]

    checkin_response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "Manual"
        },
    )

    assert checkin_response.status_code == 201

    response = client.post(
        f"/registrations/{registration_id}/check-out"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["registration_id"] == registration_id
    assert data["check_in_time"] is not None
    assert data["check_out_time"] is not None


def test_check_out_without_check_in():

    resources = create_resources()

    registration_id = resources["registration"]["id"]

    response = client.post(
        f"/registrations/{registration_id}/check-out"
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Attendee has not checked in"
    )


def test_duplicate_check_out():

    resources = create_resources()

    registration_id = resources["registration"]["id"]

    checkin_response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "Staff"
        },
    )

    assert checkin_response.status_code == 201

    first_checkout = client.post(
        f"/registrations/{registration_id}/check-out"
    )

    assert first_checkout.status_code == 200

    second_checkout = client.post(
        f"/registrations/{registration_id}/check-out"
    )

    assert second_checkout.status_code == 400

    assert (
        second_checkout.json()["detail"]
        == "Attendee has already checked out"
    )


def test_check_out_invalid_registration():

    response = client.post(
        "/registrations/999999/check-out"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Registration not found"
    )


def test_event_attendance():

    resources = create_resources()

    registration_id = resources["registration"]["id"]
    event_id = resources["event"]["id"]

    checkin_response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "QR Code"
        },
    )

    assert checkin_response.status_code == 201

    response = client.get(
        f"/events/{event_id}/attendance"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    registration_ids = [
        item["registration_id"]
        for item in data
    ]

    assert registration_id in registration_ids


def test_invalid_check_in_method():

    resources = create_resources()

    registration_id = resources["registration"]["id"]

    response = client.post(
        f"/registrations/{registration_id}/check-in",
        json={
            "check_in_method": "Invalid Method"
        },
    )

    assert response.status_code == 422


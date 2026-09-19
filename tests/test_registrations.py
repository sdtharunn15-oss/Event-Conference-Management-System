import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def register_user(role="Attendee", prefix="user"):
    email = unique_email(prefix)

    response = client.post(
        "/auth/register",
        json={
            "full_name": f"Test {prefix}",
            "email": email,
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code == 201, response.text

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Test@12345",
        },
    )

    assert login.status_code == 200, login.text

    return login.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def get_user_id(token):
    response = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    return response.json()["id"]


def create_organizer():
    return register_user(
        role="Event Organizer",
        prefix="organizer",
    )


def create_attendee():
    return register_user(
        role="Attendee",
        prefix="attendee",
    )


def create_event(
    organizer_token,
    capacity=5,
    status="Registration Open",
):
    organizer_id = get_user_id(organizer_token)

    now = datetime.utcnow()

    start_date = now + timedelta(days=2)
    end_date = start_date + timedelta(hours=8)

    registration_start = now - timedelta(days=1)
    registration_end = now + timedelta(days=1)

    response = client.post(
        "/events",
        headers=auth_headers(organizer_token),
        json={
            "event_name": f"Test Event {uuid.uuid4().hex[:8]}",
            "description": "Registration test event",
            "event_type": "Conference",
            "organizer_id": organizer_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "registration_start": registration_start.isoformat(),
            "registration_end": registration_end.isoformat(),
            "capacity": capacity,
            "status": status,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_register_for_event():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    response = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["event_id"] == event["id"]
    assert data["registration_status"] == "Confirmed"
    assert data["attendee_id"] > 0


def test_get_registrations():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    register_response = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert register_response.status_code == 201

    response = client.get(
        "/registrations",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_get_single_registration():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    registration = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    ).json()

    response = client.get(
        f"/registrations/{registration['id']}",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == registration["id"]
    assert data["event_id"] == event["id"]


def test_cancel_registration():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    registration = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    ).json()

    response = client.post(
        f"/registrations/{registration['id']}/cancel",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["registration_status"] == "Cancelled"


def test_duplicate_registration_prevented():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    first = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert first.status_code == 201

    second = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert second.status_code == 400
    assert "already registered" in second.json()["detail"]


def test_cancelled_registration_can_register_again():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    first = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert first.status_code == 201

    registration_id = first.json()["id"]

    cancel = client.post(
        f"/registrations/{registration_id}/cancel",
        headers=auth_headers(attendee_token),
    )

    assert cancel.status_code == 200
    assert cancel.json()["registration_status"] == "Cancelled"

    second = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert second.status_code == 201
    assert second.json()["id"] == registration_id
    assert second.json()["registration_status"] == "Confirmed"


def test_event_capacity_prevented():
    organizer_token = create_organizer()

    event = create_event(
        organizer_token,
        capacity=1,
    )

    attendee_1 = create_attendee()
    attendee_2 = create_attendee()

    first = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_1),
    )

    assert first.status_code == 201

    second = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_2),
    )

    assert second.status_code == 400
    assert "capacity" in second.json()["detail"].lower()


def test_registration_before_start_prevented():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    organizer_id = get_user_id(organizer_token)

    now = datetime.utcnow()

    start_date = now + timedelta(days=5)
    end_date = start_date + timedelta(hours=8)

    registration_start = now + timedelta(days=1)
    registration_end = now + timedelta(days=3)

    response = client.post(
        "/events",
        headers=auth_headers(organizer_token),
        json={
            "event_name": f"Future Registration {uuid.uuid4().hex[:8]}",
            "description": "Registration not started",
            "event_type": "Conference",
            "organizer_id": organizer_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "registration_start": registration_start.isoformat(),
            "registration_end": registration_end.isoformat(),
            "capacity": 5,
            "status": "Registration Open",
        },
    )

    assert response.status_code == 201, response.text

    event = response.json()

    registration = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert registration.status_code == 400
    assert "not started" in registration.json()["detail"].lower()


def test_registration_after_end_prevented():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    organizer_id = get_user_id(organizer_token)

    now = datetime.utcnow()

    start_date = now + timedelta(days=5)
    end_date = start_date + timedelta(hours=8)

    registration_start = now - timedelta(days=3)
    registration_end = now - timedelta(days=1)

    response = client.post(
        "/events",
        headers=auth_headers(organizer_token),
        json={
            "event_name": f"Closed Registration {uuid.uuid4().hex[:8]}",
            "description": "Registration closed",
            "event_type": "Conference",
            "organizer_id": organizer_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "registration_start": registration_start.isoformat(),
            "registration_end": registration_end.isoformat(),
            "capacity": 5,
            "status": "Registration Closed",
        },
    )

    assert response.status_code == 201, response.text

    event = response.json()

    registration = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert registration.status_code == 400
    assert "closed" in registration.json()["detail"].lower()


def test_cancelled_event_cannot_accept_registration():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(
        organizer_token,
        status="Cancelled",
    )

    response = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 400
    assert "cancelled" in response.json()["detail"].lower()


def test_non_attendee_cannot_register():
    organizer_token = create_organizer()

    event = create_event(organizer_token)

    response = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(organizer_token),
    )

    assert response.status_code == 403


def test_nonexistent_event_registration():
    attendee_token = create_attendee()

    response = client.post(
        "/events/999999/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 404


def test_cancel_other_attendee_registration_forbidden():
    organizer_token = create_organizer()

    attendee_1 = create_attendee()
    attendee_2 = create_attendee()

    event = create_event(organizer_token)

    registration = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_1),
    ).json()

    response = client.post(
        f"/registrations/{registration['id']}/cancel",
        headers=auth_headers(attendee_2),
    )

    assert response.status_code == 403


def test_cancel_attended_registration_prevented():
    organizer_token = create_organizer()
    attendee_token = create_attendee()

    event = create_event(organizer_token)

    registration = client.post(
        f"/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    ).json()

    from app.database import SessionLocal
    from app.models.registration import Registration, RegistrationStatus

    db = SessionLocal()

    try:
        db_registration = db.get(
            Registration,
            registration["id"],
        )

        db_registration.registration_status = RegistrationStatus.ATTENDED
        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/registrations/{registration['id']}/cancel",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 400
    assert "attended" in response.json()["detail"].lower()
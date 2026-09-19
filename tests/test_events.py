from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_organizer():
    email = "eventorganizer@test.com"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Event Organizer",
            "email": email,
            "password": "Organizer@12345",
            "role": "Event Organizer"
        }
    )

    if register_response.status_code == 201:
        user = register_response.json()
    else:
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "Organizer@12345"
            }
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        me_response = client.get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        assert me_response.status_code == 200

        user = me_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Organizer@12345"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return user["id"], token


def create_test_event():
    organizer_id, token = get_organizer()

    start = datetime.now() + timedelta(days=10)
    end = start + timedelta(hours=5)

    registration_start = datetime.now() + timedelta(days=1)
    registration_end = start - timedelta(days=1)

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Tech Conference 2026",
            "description": "Technology conference",
            "event_type": "Conference",
            "organizer_id": organizer_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "registration_start": registration_start.isoformat(),
            "registration_end": registration_end.isoformat(),
            "capacity": 200
        }
    )

    assert response.status_code == 201

    return response.json(), token


def test_create_event():
    event, token = create_test_event()

    assert event["event_name"] == "Tech Conference 2026"
    assert event["event_type"] == "Conference"
    assert event["capacity"] == 200
    assert event["status"] == "Draft"


def test_get_events():
    organizer_id, token = get_organizer()

    response = client.get(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_event():
    event, token = create_test_event()

    event_id = event["id"]

    response = client.get(
        f"/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == event_id
    assert data["event_name"] == "Tech Conference 2026"


def test_update_event():
    event, token = create_test_event()

    event_id = event["id"]

    response = client.put(
        f"/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Updated Tech Conference",
            "capacity": 250
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_name"] == "Updated Tech Conference"
    assert data["capacity"] == 250


def test_event_invalid_dates():
    organizer_id, token = get_organizer()

    start = datetime.now() + timedelta(days=10)
    end = start - timedelta(hours=1)

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Invalid Event",
            "description": "Invalid dates",
            "event_type": "Seminar",
            "organizer_id": organizer_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "registration_start": datetime.now().isoformat(),
            "registration_end": (
                start - timedelta(days=1)
            ).isoformat(),
            "capacity": 100
        }
    )

    assert response.status_code == 422


def test_event_invalid_capacity():
    organizer_id, token = get_organizer()

    start = datetime.now() + timedelta(days=10)
    end = start + timedelta(hours=5)

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Invalid Capacity Event",
            "description": "Invalid capacity",
            "event_type": "Workshop",
            "organizer_id": organizer_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "registration_start": datetime.now().isoformat(),
            "registration_end": (
                start - timedelta(days=1)
            ).isoformat(),
            "capacity": 0
        }
    )

    assert response.status_code == 422


def test_get_nonexistent_event():
    organizer_id, token = get_organizer()

    response = client.get(
        "/events/99999",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 404
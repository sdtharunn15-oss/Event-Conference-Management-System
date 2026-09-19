from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_organizer():
    email = "venueorganizer@test.com"
    password = "Organizer@12345"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Venue Organizer",
            "email": email,
            "password": password,
            "role": "Event Organizer",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert me_response.status_code == 200

    user = me_response.json()

    return user["id"], token


def create_test_venue():
    organizer_id, token = get_organizer()

    response = client.post(
        "/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "venue_name": "Chennai Convention Centre",
            "address": "Anna Salai, Chennai",
            "city": "Chennai",
            "capacity": 1000,
            "facilities": "Parking, WiFi, AC",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json(), token


def test_create_venue():
    venue, token = create_test_venue()

    assert venue["venue_name"] == "Chennai Convention Centre"
    assert venue["city"] == "Chennai"
    assert venue["capacity"] == 1000
    assert venue["status"] == "Active"


def test_get_venues():
    venue, token = create_test_venue()

    response = client.get(
        "/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_venue():
    venue, token = create_test_venue()

    venue_id = venue["id"]

    response = client.get(
        f"/venues/{venue_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == venue_id
    assert data["venue_name"] == "Chennai Convention Centre"


def test_update_venue():
    venue, token = create_test_venue()

    venue_id = venue["id"]

    response = client.put(
        f"/venues/{venue_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "venue_name": "Updated Convention Centre",
            "capacity": 1200,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["venue_name"] == "Updated Convention Centre"
    assert data["capacity"] == 1200


def test_create_hall():
    venue, token = create_test_venue()

    venue_id = venue["id"]

    response = client.post(
        f"/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "hall_name": "Main Hall",
            "capacity": 500,
            "floor": 1,
            "availability_status": "Available",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["venue_id"] == venue_id
    assert data["hall_name"] == "Main Hall"
    assert data["capacity"] == 500


def test_list_halls():
    venue, token = create_test_venue()

    venue_id = venue["id"]

    client.post(
        f"/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "hall_name": "Hall A",
            "capacity": 300,
            "floor": 1,
            "availability_status": "Available",
        },
    )

    response = client.get(
        f"/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_hall_capacity_cannot_exceed_venue():
    venue, token = create_test_venue()

    venue_id = venue["id"]

    response = client.post(
        f"/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "hall_name": "Oversized Hall",
            "capacity": 1500,
            "floor": 2,
            "availability_status": "Available",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Hall capacity cannot exceed venue capacity"
    )


def test_get_nonexistent_venue():
    organizer_id, token = get_organizer()

    response = client.get(
        "/venues/99999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_get_nonexistent_hall():
    organizer_id, token = get_organizer()

    response = client.get(
        "/venues/halls/99999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404
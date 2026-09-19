from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Import models so SQLAlchemy registers their tables
from app.models.user import User
from app.models.event import Event
from app.models.ticket import Ticket


TEST_DATABASE_URL = "sqlite:///./test_event_conference.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# IMPORTANT:
# Create all tables, including tickets.
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def unique_email():
    return f"ticket_{datetime.utcnow().timestamp()}@example.com"


def register_user(
    email: str,
    role: str = "Event Organizer"
):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Ticket Test User",
            "email": email,
            "password": "Test@12345",
            "phone": "9876543210",
            "role": role,
        },
    )

    assert response.status_code in [201, 400]

    return email


def login_user(email: str):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_organizer():
    email = unique_email()

    register_user(
        email=email,
        role="Event Organizer",
    )

    token = login_user(email)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    return token, response.json()["id"]


def create_event(
    token: str,
    organizer_id: int
):
    now = datetime.utcnow()

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Ticket Test Conference",
            "description": "Testing ticket management",
            "event_type": "Conference",
            "organizer_id": organizer_id,
            "start_date": (
                now + timedelta(days=10)
            ).isoformat(),
            "end_date": (
                now + timedelta(days=11)
            ).isoformat(),
            "registration_start": (
                now - timedelta(days=1)
            ).isoformat(),
            "registration_end": (
                now + timedelta(days=9)
            ).isoformat(),
            "capacity": 100,
            "status": "Published",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def ticket_payload():
    now = datetime.utcnow()

    return {
        "ticket_type": "Standard",
        "price": 500,
        "quantity": 50,
        "available_quantity": 50,
        "sale_start": (
            now - timedelta(days=1)
        ).isoformat(),
        "sale_end": (
            now + timedelta(days=5)
        ).isoformat(),
    }


def test_create_ticket():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=ticket_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["event_id"] == event_id
    assert data["ticket_type"] == "Standard"
    assert data["price"] == 500
    assert data["quantity"] == 50
    assert data["available_quantity"] == 50


def test_get_event_tickets():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=ticket_payload(),
    )

    assert response.status_code == 201

    response = client.get(
        f"/events/{event_id}/tickets"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_update_ticket():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=ticket_payload(),
    )

    assert response.status_code == 201

    ticket_id = response.json()["id"]

    response = client.put(
        f"/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "price": 750,
            "quantity": 40,
            "available_quantity": 40,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["price"] == 750
    assert data["quantity"] == 40
    assert data["available_quantity"] == 40


def test_negative_ticket_price_rejected():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    payload = ticket_payload()
    payload["price"] = -100

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_negative_ticket_quantity_rejected():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    payload = ticket_payload()
    payload["quantity"] = -10

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_available_quantity_cannot_exceed_quantity():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    payload = ticket_payload()

    payload["quantity"] = 20
    payload["available_quantity"] = 30

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_ticket_sale_end_before_sale_start_rejected():

    token, organizer_id = create_organizer()

    event_id = create_event(
        token,
        organizer_id
    )

    now = datetime.utcnow()

    payload = ticket_payload()

    payload["sale_start"] = (
        now + timedelta(days=5)
    ).isoformat()

    payload["sale_end"] = (
        now + timedelta(days=2)
    ).isoformat()

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_nonexistent_event_rejected():

    token, _ = create_organizer()

    response = client.post(
        "/events/999999/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=ticket_payload(),
    )

    assert response.status_code == 404
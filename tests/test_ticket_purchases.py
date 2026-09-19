from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

from app.models.user import User
from app.models.event import Event
from app.models.ticket import Ticket
from app.models.ticket_purchase import TicketPurchase


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
    return f"purchase_{datetime.utcnow().timestamp()}@example.com"


def create_user():
    email = unique_email()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Purchase Test User",
            "email": email,
            "password": "Test@12345",
            "phone": "9876543210",
            "role": "Event Organizer",
        },
    )

    assert response.status_code in [201, 400]

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    user_id = response.json()["id"]

    return token, user_id


def create_event(token, organizer_id):
    now = datetime.utcnow()

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Purchase Test Event",
            "description": "Ticket purchase test",
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


def create_ticket(token, event_id):
    now = datetime.utcnow()

    response = client.post(
        f"/events/{event_id}/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_type": "Standard",
            "price": 500,
            "quantity": 20,
            "available_quantity": 20,
            "sale_start": (
                now - timedelta(days=1)
            ).isoformat(),
            "sale_end": (
                now + timedelta(days=5)
            ).isoformat(),
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def setup_purchase():
    token, user_id = create_user()

    event_id = create_event(
        token,
        user_id
    )

    ticket_id = create_ticket(
        token,
        event_id
    )

    return token, user_id, event_id, ticket_id


def test_purchase_ticket():
    token, _, _, ticket_id = setup_purchase()

    response = client.post(
        f"/tickets/{ticket_id}/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": ticket_id,
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["ticket_id"] == ticket_id
    assert data["quantity"] == 2
    assert data["total_amount"] == 1000


def test_ticket_quantity_reduced_after_purchase():
    token, _, event_id, ticket_id = setup_purchase()

    response = client.post(
        f"/tickets/{ticket_id}/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": ticket_id,
            "quantity": 3,
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/events/{event_id}/tickets"
    )

    assert response.status_code == 200

    tickets = response.json()

    ticket = next(
        item for item in tickets
        if item["id"] == ticket_id
    )

    assert ticket["available_quantity"] == 17


def test_purchase_more_than_available_rejected():
    token, _, _, ticket_id = setup_purchase()

    response = client.post(
        f"/tickets/{ticket_id}/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": ticket_id,
            "quantity": 999,
        },
    )

    assert response.status_code == 400


def test_invalid_quantity_rejected():
    token, _, _, ticket_id = setup_purchase()

    response = client.post(
        f"/tickets/{ticket_id}/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": ticket_id,
            "quantity": 0,
        },
    )

    assert response.status_code == 422


def test_nonexistent_ticket_rejected():
    token, _, _, _ = setup_purchase()

    response = client.post(
        "/tickets/999999/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": 999999,
            "quantity": 1,
        },
    )

    assert response.status_code == 404


def test_get_my_purchases():
    token, _, _, ticket_id = setup_purchase()

    purchase_response = client.post(
        f"/tickets/{ticket_id}/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": ticket_id,
            "quantity": 1,
        },
    )

    assert purchase_response.status_code == 201

    response = client.get(
        "/ticket-purchases",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_single_purchase():
    token, _, _, ticket_id = setup_purchase()

    purchase_response = client.post(
        f"/tickets/{ticket_id}/purchase",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_id": ticket_id,
            "quantity": 1,
        },
    )

    assert purchase_response.status_code == 201

    purchase_id = purchase_response.json()["id"]

    response = client.get(
        f"/ticket-purchases/{purchase_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == purchase_id
    assert data["ticket_id"] == ticket_id
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


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
    return f"payment_{datetime.utcnow().timestamp()}@example.com"


def create_user():
    email = unique_email()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Payment Test User",
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

    return token, response.json()["id"]


def create_event(token, organizer_id):
    now = datetime.utcnow()

    response = client.post(
        "/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Payment Test Event",
            "description": "Payment testing",
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


def create_purchase(token, ticket_id):
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

    return response.json()["id"]


def setup_payment():
    token, user_id = create_user()

    event_id = create_event(
        token,
        user_id,
    )

    ticket_id = create_ticket(
        token,
        event_id,
    )

    purchase_id = create_purchase(
        token,
        ticket_id,
    )

    return token, user_id, purchase_id


def test_create_payment():
    token, _, purchase_id = setup_payment()

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": purchase_id,
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["purchase_id"] == purchase_id
    assert data["amount"] == 1000
    assert data["payment_method"] == "UPI"

    # Actual project enum value
    assert data["status"] == "Completed"

    assert data["transaction_id"] is not None
    assert data["paid_at"] is not None


def test_get_my_payments():
    token, _, purchase_id = setup_payment()

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": purchase_id,
            "payment_method": "Card",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_single_payment():
    token, _, purchase_id = setup_payment()

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": purchase_id,
            "payment_method": "Net Banking",
        },
    )

    assert response.status_code == 201

    payment_id = response.json()["id"]

    response = client.get(
        f"/payments/{payment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["purchase_id"] == purchase_id


def test_duplicate_payment_rejected():
    token, _, purchase_id = setup_payment()

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": purchase_id,
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": purchase_id,
            "payment_method": "Card",
        },
    )

    assert response.status_code == 400


def test_nonexistent_purchase_rejected():
    token, _, _ = setup_payment()

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": 999999,
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 404


def test_update_payment_status():
    token, _, purchase_id = setup_payment()

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "purchase_id": purchase_id,
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    payment_id = response.json()["id"]

    response = client.put(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Refunded",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["status"] == "Refunded"


def test_nonexistent_payment_rejected():
    token, _, _ = setup_payment()

    response = client.get(
        "/payments/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404
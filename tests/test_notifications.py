from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def create_user():
    unique_id = uuid4().hex[:8]

    email = f"notification_{unique_id}@test.com"
    password = "Test@12345"

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Notification User",
            "email": email,
            "password": password,
            "role": "Attendee",
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


def create_notification(token):
    response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "user_id": get_user_id(token),
            "notification_type": "Registration Confirmation",
            "title": "Registration Confirmed",
            "message": "Your event registration has been confirmed.",
        },
    )

    assert response.status_code == 201

    return response.json()


def get_user_id(token):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def test_create_notification():
    token = create_user()

    notification = create_notification(token)

    assert notification["title"] == "Registration Confirmed"
    assert (
        notification["notification_type"]
        == "Registration Confirmation"
    )
    assert notification["message"] == (
        "Your event registration has been confirmed."
    )
    assert notification["is_read"] is False


def test_get_my_notifications():
    token = create_user()

    create_notification(token)

    response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_get_unread_notifications():
    token = create_user()

    notification = create_notification(token)

    response = client.get(
        "/notifications/unread",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    notifications = response.json()

    assert isinstance(notifications, list)
    assert any(
        item["id"] == notification["id"]
        for item in notifications
    )


def test_get_single_notification():
    token = create_user()

    notification = create_notification(token)

    notification_id = notification["id"]

    response = client.get(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == notification_id
    assert response.json()["title"] == "Registration Confirmed"


def test_mark_notification_as_read():
    token = create_user()

    notification = create_notification(token)

    notification_id = notification["id"]

    response = client.put(
        f"/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "is_read": True
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == notification_id
    assert response.json()["is_read"] is True


def test_mark_notification_as_unread():
    token = create_user()

    notification = create_notification(token)

    notification_id = notification["id"]

    read_response = client.put(
        f"/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "is_read": True
        },
    )

    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    unread_response = client.put(
        f"/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "is_read": False
        },
    )

    assert unread_response.status_code == 200
    assert unread_response.json()["is_read"] is False


def test_notification_not_found():
    token = create_user()

    response = client.get(
        "/notifications/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


def test_delete_notification():
    token = create_user()

    notification = create_notification(token)

    notification_id = notification["id"]

    response = client.delete(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert get_response.status_code == 404


def test_cannot_access_other_users_notification():
    token_one = create_user()
    token_two = create_user()

    notification = create_notification(token_one)

    notification_id = notification["id"]

    response = client.get(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {token_two}"
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can only access your own notifications"
    )


def test_cannot_create_notification_for_other_user():
    token_one = create_user()
    token_two = create_user()

    user_two_id = get_user_id(token_two)

    response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token_one}"
        },
        json={
            "user_id": user_two_id,
            "notification_type": "Payment Success",
            "title": "Payment Successful",
            "message": "Your payment was successful.",
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can only create notifications for yourself"
    )


def test_delete_other_users_notification():
    token_one = create_user()
    token_two = create_user()

    notification = create_notification(token_one)

    notification_id = notification["id"]

    response = client.delete(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {token_two}"
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can only access your own notifications"
    )


def test_invalid_notification_type():
    token = create_user()

    response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "user_id": get_user_id(token),
            "notification_type": "Invalid Notification",
            "title": "Invalid",
            "message": "Invalid notification type.",
        },
    )

    assert response.status_code == 422
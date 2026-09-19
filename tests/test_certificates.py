from datetime import date

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_certificate():
    response = client.post(
        "/certificates/generate/1"
    )

    assert response.status_code in (200, 201, 400, 404)


def test_get_certificate():
    response = client.get(
        "/certificates/1"
    )

    assert response.status_code in (200, 404)


def test_get_attendee_certificates():
    response = client.get(
        "/attendees/1/certificates"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_generate_certificate_invalid_registration():
    response = client.post(
        "/certificates/generate/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Registration not found"


def test_get_invalid_certificate():
    response = client.get(
        "/certificates/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate not found"


def test_get_certificates_for_invalid_attendee():
    response = client.get(
        "/attendees/999999/certificates"
    )

    assert response.status_code == 200
    assert response.json() == []
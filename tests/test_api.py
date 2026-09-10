"""Minimal example tests for the FastAPI service. Add your own for Task 1 / Task 4."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_context():
    response = client.get("/context")
    assert response.status_code == 200
    assert "location" in response.json()


def test_register_and_list_call():
    payload = {"room": "patient-4821", "transcript": "...", "duration_seconds": 12.3}
    response = client.post("/calls", json=payload)
    assert response.status_code == 200
    assert response.json()["room"] == "patient-4821"

    listed = client.get("/calls").json()
    assert any(c["room"] == "patient-4821" for c in listed)

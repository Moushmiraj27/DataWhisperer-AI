from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_check_returns_service_metadata() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_check_includes_security_headers_and_request_id() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health", headers={"x-request-id": "test-request"})

    assert response.headers["x-request-id"] == "test-request"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"

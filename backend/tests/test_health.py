from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ORBIT AI Industrial Copilot API"
    assert payload["environment"] == "test"
    assert payload["version"] == "0.1.0"
    assert "timestamp" in payload


def test_versioned_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

"""Tests for health and root endpoints."""


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Bem-vindo" in data["message"]
    assert "version" in data


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert data["services"]["database"] == "healthy"


def test_health_reports_minio_state(client, monkeypatch):
    monkeypatch.setattr("app.core.storage.storage_service.ping", lambda: False)
    data = client.get("/api/v1/health").json()
    assert data["services"]["minio"] == "degraded"
    assert data["status"] == "degraded"

"""Tests for interactive API documentation and OpenAPI schema exposure by environment (#172)."""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_ENDPOINTS = ("/docs", "/redoc", f"{settings.API_V1_STR}/openapi.json")


@pytest.mark.parametrize("endpoint", DOC_ENDPOINTS)
def test_openapi_and_interactive_docs_return_404_in_production(client, monkeypatch, endpoint):
    """Issue #172: com ENVIRONMENT=production, /docs, /redoc e openapi.json retornam 404."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_ACCESS", False)

    response = client.get(endpoint)
    assert response.status_code == 404

    prod_app = create_app()
    assert prod_app.docs_url is None
    assert prod_app.redoc_url is None
    assert prod_app.openapi_url is None
    with TestClient(prod_app) as prod_client:
        assert prod_client.get(endpoint).status_code == 404
        assert prod_client.get("/").json()["docs"] is None


@pytest.mark.parametrize("environment", ["development", "test"])
@pytest.mark.parametrize("endpoint", DOC_ENDPOINTS)
def test_openapi_and_interactive_docs_stay_available_outside_production(
    client, monkeypatch, environment, endpoint
):
    """Issue #172: fora de producao (development e test), /docs, /redoc e openapi ficam ativos."""
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)

    response = client.get(endpoint)
    assert response.status_code == 200
    if endpoint.endswith("/openapi.json"):
        payload = response.json()
        assert "openapi" in payload
        assert "paths" in payload

    non_prod_app = create_app()
    assert non_prod_app.docs_url == "/docs"
    assert non_prod_app.redoc_url == "/redoc"
    assert non_prod_app.openapi_url == f"{settings.API_V1_STR}/openapi.json"


def test_tls_termination_runbook_documents_location_owner_and_openssl_verification():
    """Issue #172: runbook em docs/ identifica onde termina o TLS, responsavel e openssl."""
    devops_doc = (REPO_ROOT / "docs" / "development" / "devops.md").read_text(encoding="utf-8")
    security_doc = (REPO_ROOT / "docs" / "planning" / "governance-security.md").read_text(
        encoding="utf-8"
    )

    assert "TLS 1.3" in devops_doc
    assert "openssl s_client -connect" in devops_doc
    assert "-tls1_3" in devops_doc
    assert "@conformia-bndes/devops" in devops_doc
    assert "ENVIRONMENT=production" in security_doc
    assert "/api/v1/openapi.json" in security_doc

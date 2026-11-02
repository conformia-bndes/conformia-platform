"""Contrato da API: fuso nos timestamps e respostas de erro documentadas no OpenAPI."""

from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.main import app
from app.schemas.document import DocumentListItem
from app.schemas.types import UTCDateTime
from pydantic import BaseModel

PUBLIC_PATHS = {"/", f"{settings.API_V1_STR}/health"}


class _Holder(BaseModel):
    moment: UTCDateTime


def test_naive_timestamp_is_serialized_as_utc():
    """O banco guarda datetime.utcnow() (sem fuso); a API precisa devolver RFC 3339 com fuso."""
    holder = _Holder(moment=datetime(2026, 11, 2, 4, 26, 27, 749387))
    assert holder.moment.tzinfo is timezone.utc
    assert holder.model_dump_json().endswith('+00:00"}') or 'Z"' in holder.model_dump_json()


def test_aware_timestamp_is_preserved():
    moment = datetime(2026, 11, 2, 1, 0, tzinfo=timezone.utc)
    assert _Holder(moment=moment).moment == moment


def test_document_list_item_created_at_has_timezone():
    item = DocumentListItem(
        id="x",
        original_filename="a.pdf",
        status="COMPLETED",
        created_at=datetime(2026, 11, 2, 4, 26, 27),
        file_size=1,
    )
    assert item.created_at.tzinfo is not None


@pytest.mark.parametrize(
    "path,operations",
    [(path, ops) for path, ops in app.openapi()["paths"].items() if path not in PUBLIC_PATHS],
)
def test_protected_routes_document_error_responses(path, operations):
    """Clientes gerados a partir do OpenAPI precisam conhecer os erros 401, 403 e 404."""
    for method, spec in operations.items():
        responses = spec["responses"]
        for code in ("401", "403", "404"):
            assert code in responses, f"{method.upper()} {path} nao documenta {code}"
        schema = responses["404"]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/HTTPErrorResponse")


@pytest.mark.parametrize("path", ["/api/v1/documents", "/api/v1/compliance/audit-trail"])
@pytest.mark.parametrize(
    "query",
    [
        "limit=9223372036854775808",  # estoura o inteiro do banco (achado do fuzzing)
        "limit=100000",
        "limit=0",
        "limit=-1",
        "skip=-1",
        "skip=9223372036854775808",
    ],
)
def test_pagination_rejects_out_of_range_values(client, path, query):
    """Paginacao sem limite maximo permitia 500 por estouro de inteiro e leitura da tabela toda."""
    assert client.get(f"{path}?{query}").status_code == 422


@pytest.mark.parametrize("path", ["/api/v1/documents", "/api/v1/compliance/audit-trail"])
def test_pagination_accepts_the_documented_range(client, path):
    assert client.get(f"{path}?skip=0&limit=200").status_code == 200
    assert client.get(path).status_code == 200


def test_database_outage_returns_503_with_retry_after(client):
    """Postgres fora do ar e falha temporaria de dependencia: 503, nunca 500."""
    from sqlalchemy.exc import OperationalError

    from app.db.session import get_db

    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        yield  # pragma: no cover - torna a funcao um gerador, como o get_db real

    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.get("/api/v1/documents")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert "connection refused" not in response.text  # sem vazar detalhes internos


def test_storage_ping_fails_fast_when_minio_is_down(monkeypatch):
    """Com o MinIO fora do ar o healthcheck responde em segundos, sem travar a requisicao."""
    import time

    from app.core.storage import StorageService

    service = StorageService()
    service.endpoint = "127.0.0.1:9"  # porta sem servico: conexao recusada
    started = time.monotonic()
    assert service.ping() is False
    assert time.monotonic() - started < 5


def test_storage_ping_creates_missing_bucket(monkeypatch):
    """MinIO novo (sem bucket) e saudavel: o ping cria o bucket em vez de ficar degradado."""
    from app.core.storage import StorageService

    class FakeMinio:
        def __init__(self):
            self.created = []

        def bucket_exists(self, name):
            return name in self.created

        def make_bucket(self, name):
            self.created.append(name)

    fake = FakeMinio()
    service = StorageService()
    monkeypatch.setattr(service, "_build_client", lambda *args, **kwargs: fake)
    assert service.ping() is True
    assert fake.created == [service.bucket_name]
    assert service.ping() is True  # segunda chamada: bucket ja existe, nada a criar
    assert fake.created == [service.bucket_name]

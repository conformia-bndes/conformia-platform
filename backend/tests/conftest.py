"""Pytest configuration and test fixtures."""

import os

# Segredos nao tem default no codigo; os testes injetam valores descartaveis ANTES de
# importar a aplicacao (a Settings valida o ambiente no import).
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("POSTGRES_PASSWORD", "test-postgres-password")
os.environ.setdefault("MINIO_ROOT_USER", "test-minio-user")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test-minio-password")
os.environ.setdefault("ENVIRONMENT", "test")
# Os testes usam o cliente sem chave; testes de autenticacao desligam este opt-in.
os.environ.setdefault("ALLOW_ANONYMOUS_ACCESS", "true")

from types import SimpleNamespace  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.main import app  # noqa: E402
from app.db.session import Base, get_db  # noqa: E402

# Banco SQLite em memória isolado para os testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True, scope="function")
def _no_network(monkeypatch):
    """Desliga chamadas de rede reais (MinIO, Redis, Postgres) em todos os testes.

    Nenhum teste unitario depende de servicos externos. Assim o health endpoint e os
    uploads nao esperam timeouts de MinIO/Redis.
    """
    from app.core import storage as storage_module
    from app.api.v1.endpoints import health as health_module

    bucket = storage_module.storage_service.bucket_name

    monkeypatch.setattr(storage_module.storage_service, "ping", lambda: True)
    monkeypatch.setattr(
        storage_module.storage_service,
        "upload_file",
        lambda file_data, object_name, content_type="application/pdf": (
            f"s3://{bucket}/{object_name}"
        ),
    )
    monkeypatch.setattr(
        storage_module.storage_service,
        "download_file",
        lambda object_name, destination_path: None,
    )
    monkeypatch.setattr(
        health_module,
        "_redis_client",
        lambda: SimpleNamespace(ping=lambda: True),
    )


@pytest.fixture(scope="function")
def db_session():
    """Cria uma base de dados limpa para cada caso de teste."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Retorna um TestClient do FastAPI com a dependência get_db mockada para a base em memória."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

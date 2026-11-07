"""Migrations Alembic: bancos novos, bancos legados (create_all), upgrade/downgrade e PostgreSQL.

Os testes em SQLite rodam sempre. Os de PostgreSQL exigem um banco DESCARTAVEL em
MIGRATION_TEST_DATABASE_URL (o CI sobe um servico; localmente, qualquer instancia temporaria):
o esquema `public` do banco indicado e apagado a cada teste.
"""

import os
import threading

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.db import models  # noqa: F401  (registra as tabelas no metadata)
from app.db.migrate import (
    BASELINE_REVISION,
    BASELINE_TABLES,
    LegacySchemaError,
    alembic_config,
    migrate,
)
from app.db.session import Base

HEAD = "002_review_events"
ALL_TABLES = BASELINE_TABLES | {"review_events"}

POSTGRES_URL = os.environ.get("MIGRATION_TEST_DATABASE_URL")
requires_postgres = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="defina MIGRATION_TEST_DATABASE_URL com um PostgreSQL descartavel",
)


def _tables(engine):
    return set(inspect(engine).get_table_names())


def _version(engine):
    with engine.connect() as connection:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar()


def _run(engine, revision, direction):
    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        getattr(command, direction)(config, revision)


@pytest.fixture
def sqlite_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migracoes.db'}")
    yield engine
    engine.dispose()


@pytest.fixture
def postgres_engine():
    engine = create_engine(POSTGRES_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    yield engine
    engine.dispose()


def _create_legacy(engine, with_reviews):
    """Banco como o create_all antigo deixava: tabelas, mas sem alembic_version."""
    tables = [t for name, t in Base.metadata.tables.items() if name in BASELINE_TABLES]
    if with_reviews:
        tables.append(Base.metadata.tables["review_events"])
    Base.metadata.create_all(bind=engine, tables=tables)


@pytest.mark.parametrize(
    "engine_fixture", ["sqlite_engine", pytest.param("postgres_engine", marks=requires_postgres)]
)
class TestMigrations:
    @pytest.fixture
    def engine(self, request, engine_fixture):
        return request.getfixturevalue(engine_fixture)

    def test_empty_database_is_migrated_to_head(self, engine):
        assert migrate(engine) is None
        assert ALL_TABLES <= _tables(engine)
        assert _version(engine) == HEAD

    def test_migrate_is_idempotent(self, engine):
        migrate(engine)
        migrate(engine)
        assert _version(engine) == HEAD

    def test_legacy_database_without_reviews_receives_review_events(self, engine):
        _create_legacy(engine, with_reviews=False)
        assert "review_events" not in _tables(engine)

        assert migrate(engine) == BASELINE_REVISION

        assert "review_events" in _tables(engine)
        assert _version(engine) == HEAD

    def test_legacy_database_with_reviews_is_only_stamped(self, engine):
        _create_legacy(engine, with_reviews=True)
        assert migrate(engine) == HEAD
        assert _version(engine) == HEAD

    def test_legacy_data_survives(self, engine):
        _create_legacy(engine, with_reviews=False)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO documents (id, filename, original_filename, content_type, "
                    "file_size, storage_path, status, created_at, updated_at) VALUES "
                    "('d1', 'a.pdf', 'a.pdf', 'application/pdf', 10, 'p/a.pdf', 'PENDING', "
                    "'2026-01-01', '2026-01-01')"
                )
            )
        migrate(engine)
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM documents")).scalar() == 1

    def test_partial_legacy_schema_is_rejected(self, engine):
        Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables["documents"]])
        with pytest.raises(LegacySchemaError) as exc:
            migrate(engine)
        assert "compliance_checks" in str(exc.value)
        assert "alembic_version" not in _tables(engine)

    def test_002_downgrade_and_upgrade_round_trip(self, engine):
        migrate(engine)
        _run(engine, BASELINE_REVISION, "downgrade")
        assert "review_events" not in _tables(engine)
        assert BASELINE_TABLES <= _tables(engine)
        assert _version(engine) == BASELINE_REVISION

        _run(engine, "head", "upgrade")
        assert "review_events" in _tables(engine)
        assert _version(engine) == HEAD

    def test_migrations_match_the_models(self, engine):
        """Falha se alguem alterar um modelo sem criar a migration correspondente."""
        migrate(engine)
        with engine.connect() as connection:
            diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert diff == []


@requires_postgres
def test_concurrent_runs_are_serialized_by_advisory_lock(postgres_engine):
    errors = []

    def run():
        try:
            migrate(postgres_engine)
        except Exception as exc:  # noqa: BLE001 - o teste reporta qualquer falha da thread
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    assert errors == []
    assert _version(postgres_engine) == HEAD


def test_application_startup_does_not_create_tables(monkeypatch):
    """O esquema vem so das migrations: subir a API nao pode chamar create_all."""
    from app.main import app

    def forbidden(*args, **kwargs):
        raise AssertionError("create_all nao deve ser chamado na inicializacao")

    monkeypatch.setattr(Base.metadata, "create_all", forbidden)
    with TestClient(app):
        pass

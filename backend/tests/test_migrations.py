"""Migrations Alembic: bancos novos, bancos legados (create_all), upgrade/downgrade e PostgreSQL.

Os testes em SQLite rodam sempre. Os de PostgreSQL exigem um banco DESCARTAVEL em
MIGRATION_TEST_DATABASE_URL (o CI sobe um servico; localmente, qualquer instancia temporaria):
o esquema `public` do banco indicado e apagado a cada teste.
"""

import os
from pathlib import Path
import threading

import pytest
import yaml
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

from app.db import models  # noqa: F401  (registra as tabelas no metadata)
from app.db.migrate import (
    BASELINE_REVISION,
    BASELINE_TABLES,
    REVIEWS_REVISION,
    LegacySchemaError,
    alembic_config,
    migrate,
)
from app.db.session import Base

HEAD = "003_immutable_audit_and_checks"
ALL_TABLES = BASELINE_TABLES | {"review_events"}
DB_MUTATION_ERRORS = (IntegrityError, OperationalError, ProgrammingError)

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

    def test_legacy_database_with_reviews_is_stamped_and_upgraded_to_head(self, engine):
        _create_legacy(engine, with_reviews=True)
        assert migrate(engine) == REVIEWS_REVISION
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

    def test_003_and_002_downgrade_and_upgrade_round_trip(self, engine):
        migrate(engine)
        assert _version(engine) == HEAD

        # Downgrade 003 -> 002 (remove triggers e CHECK constraints)
        _run(engine, REVIEWS_REVISION, "downgrade")
        assert _version(engine) == REVIEWS_REVISION
        assert "review_events" in _tables(engine)

        # Downgrade 002 -> 001
        _run(engine, BASELINE_REVISION, "downgrade")
        assert "review_events" not in _tables(engine)
        assert BASELINE_TABLES <= _tables(engine)
        assert _version(engine) == BASELINE_REVISION

        # Upgrade completo 001 -> head (003)
        _run(engine, "head", "upgrade")
        assert "review_events" in _tables(engine)
        assert _version(engine) == HEAD

    def test_audit_logs_and_review_events_reject_update_and_delete(self, engine):
        """RNF03 (#167): UPDATE e DELETE falham na propria persistencia (append-only)."""
        migrate(engine)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO documents (id, filename, original_filename, content_type, "
                    "file_size, storage_path, status, created_at, updated_at) VALUES "
                    "('d-imm', 'a.pdf', 'a.pdf', 'application/pdf', 10, 'p/a.pdf', 'COMPLETED', "
                    "'2026-01-01', '2026-01-01')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO audit_logs (id, entity_type, entity_id, action, performed_by, "
                    "created_at) VALUES ('a1', 'DOCUMENT', 'd-imm', 'DOCUMENT_UPLOADED', "
                    "'ana', '2026-01-01')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO review_events (id, document_id, event_type, decision, "
                    "justification, actor_id, actor_role, created_at) VALUES "
                    "('r1', 'd-imm', 'PROPOSED', 'APPROVE', 'Justificativa tecnica valida.', "
                    "'ana', 'ANALISTA', '2026-01-01')"
                )
            )

        with pytest.raises(DB_MUTATION_ERRORS):
            with engine.begin() as conn:
                conn.execute(text("UPDATE audit_logs SET action = 'ALTERED' WHERE id = 'a1'"))

        with pytest.raises(DB_MUTATION_ERRORS):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM audit_logs WHERE id = 'a1'"))

        with pytest.raises(DB_MUTATION_ERRORS):
            with engine.begin() as conn:
                conn.execute(text("UPDATE review_events SET decision = 'REJECT' WHERE id = 'r1'"))

        with pytest.raises(DB_MUTATION_ERRORS):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM review_events WHERE id = 'r1'"))

        with engine.connect() as conn:
            assert conn.execute(text("SELECT count(*) FROM audit_logs")).scalar() == 1
            assert conn.execute(text("SELECT count(*) FROM review_events")).scalar() == 1

    def test_domain_check_constraints_reject_invalid_values(self, engine):
        """AUD-18a (#167): valores fora do dominio de status, event_type, decision e actor_role."""
        migrate(engine)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO documents (id, filename, original_filename, content_type, "
                    "file_size, storage_path, status, created_at, updated_at) VALUES "
                    "('d-ok', 'a.pdf', 'a.pdf', 'application/pdf', 10, 'p/a.pdf', 'COMPLETED', "
                    "'2026-01-01', '2026-01-01')"
                )
            )

        # documents.status invalido
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO documents (id, filename, original_filename, content_type, "
                        "file_size, storage_path, status, created_at, updated_at) VALUES "
                        "('d-bad', 'b.pdf', 'b.pdf', 'application/pdf', 10, 'p/b.pdf', "
                        "'STATUS_INVALIDO', '2026-01-01', '2026-01-01')"
                    )
                )

        # compliance_checks.status invalido
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO compliance_checks (id, document_id, rule_id, rule_title, "
                        "category, status, confidence_score, checker_type, created_at) VALUES "
                        "('c-bad', 'd-ok', 'RULE-BNDES-001', 'CND', 'FISCAL', 'APROVADO_FORA', "
                        "1.0, 'DETERMINISTIC', '2026-01-01')"
                    )
                )

        # review_events.event_type invalido
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO review_events (id, document_id, event_type, decision, "
                        "justification, actor_id, actor_role, created_at) VALUES "
                        "('r-bad-type', 'd-ok', 'INVENTADO', 'APPROVE', 'x', 'ana', 'ANALISTA', "
                        "'2026-01-01')"
                    )
                )

        # review_events.decision invalida
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO review_events (id, document_id, event_type, decision, "
                        "justification, actor_id, actor_role, created_at) VALUES "
                        "('r-bad-dec', 'd-ok', 'PROPOSED', 'TALVEZ', 'x', 'ana', 'ANALISTA', "
                        "'2026-01-01')"
                    )
                )

        # review_events.actor_role invalido
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO review_events (id, document_id, event_type, decision, "
                        "justification, actor_id, actor_role, created_at) VALUES "
                        "('r-bad-role', 'd-ok', 'PROPOSED', 'APPROVE', 'x', 'ana', 'ROOT', "
                        "'2026-01-01')"
                    )
                )

    def test_migrations_match_the_models(self, engine):
        """Falha se alguem alterar um modelo sem criar a migration correspondente."""
        migrate(engine)
        with engine.connect() as connection:
            diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert diff == []


def test_ci_backend_workflow_runs_migration_tests_against_postgres():
    """Issue #167: garante que o CI fornece PostgreSQL real para test_migrations.py."""
    ci_path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci-backend.yml"
    data = yaml.safe_load(ci_path.read_text(encoding="utf-8"))
    test_job = data["jobs"]["test"]
    assert "postgres" in test_job["services"]
    pytest_step = next(s for s in test_job["steps"] if "pytest" in s.get("name", "").lower())
    assert "MIGRATION_TEST_DATABASE_URL" in (pytest_step.get("env") or {})


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

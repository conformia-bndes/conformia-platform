"""Aplica as migrations Alembic pendentes: `python -m app.db.migrate`.

Roda como etapa dedicada antes da API e do worker (servico `migrate` do compose, `make migrate`).
A aplicacao nao cria tabelas por conta propria: o esquema vem somente das migrations.

Bancos criados antes das migrations (via `create_all`) tem as tabelas mas nao a tabela
`alembic_version`; um `upgrade head` direto falharia com "table already exists". Nesses casos o
esquema existente e carimbado na revisao equivalente e o upgrade aplica apenas o que falta.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.inspection import inspect

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Revisao 001 criou estas tabelas; a 002 acrescentou review_events.
BASELINE_REVISION = "001_initial_schema"
BASELINE_TABLES = frozenset({"documents", "compliance_checks", "audit_logs"})
REVIEW_TABLE = "review_events"

# Chave do advisory lock do PostgreSQL: serializa execucoes simultaneas (ex.: duas replicas).
MIGRATION_LOCK_KEY = 7_270_501


class LegacySchemaError(RuntimeError):
    """Esquema existente sem alembic_version que nao corresponde a nenhuma revisao conhecida."""


def alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    # Caminho absoluto: independe do diretorio de trabalho do processo.
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("version_locations", str(BACKEND_DIR / "alembic" / "versions"))
    return config


def detect_legacy_revision(connection: Connection, head_revision: str) -> str | None:
    """Revisao a carimbar em um banco criado por create_all, ou None se nao for o caso."""
    tables = set(inspect(connection).get_table_names())
    if "alembic_version" in tables:
        return None
    present = BASELINE_TABLES & tables
    if not present:
        return None
    if present != BASELINE_TABLES:
        raise LegacySchemaError(
            "Banco com esquema parcial e sem alembic_version (faltam: "
            f"{', '.join(sorted(BASELINE_TABLES - present))}). Restaure um backup ou "
            "recrie o banco; nao e seguro adivinhar a revisao."
        )
    return head_revision if REVIEW_TABLE in tables else BASELINE_REVISION


def migrate(engine: Engine) -> str | None:
    """Leva o banco a `head`. Retorna a revisao carimbada, se o banco era legado."""
    config = alembic_config()
    head_revision = ScriptDirectory.from_config(config).get_current_head()

    # O lock vive em uma conexao propria (autocommit): nao participa da transacao de DDL.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as lock_connection:
        use_lock = engine.dialect.name == "postgresql"
        if use_lock:
            lock_connection.execute(
                text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK_KEY}
            )
        try:
            with engine.begin() as connection:
                config.attributes["connection"] = connection
                stamped = detect_legacy_revision(connection, head_revision)
                if stamped:
                    command.stamp(config, stamped)
                command.upgrade(config, "head")
            return stamped
        finally:
            if use_lock:
                lock_connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK_KEY}
                )


def main() -> None:
    from app.db.session import engine

    stamped = migrate(engine)
    if stamped:
        print(f"Banco existente carimbado em {stamped} (criado antes das migrations).", flush=True)
    print("Migrations aplicadas: banco em 'head'.", flush=True)


if __name__ == "__main__":
    main()

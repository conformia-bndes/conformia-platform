"""Immutable append-only triggers for audit_logs/review_events and domain CHECK constraints

Revision ID: 003_immutable_audit_and_checks
Revises: 002_review_events
Create Date: 2026-11-27 23:00:00.000000

RNF03 (Issue #167):
- Bloqueia UPDATE e DELETE em `audit_logs` e `review_events` na propria persistencia
  via triggers BEFORE UPDATE / BEFORE DELETE (inclusive para a conexao dona do esquema
  usada pela aplicacao).
- Impoe CHECK constraints para os dominios validos de `documents.status`,
  `compliance_checks.status`, `review_events.event_type`, `review_events.decision`
  e `review_events.actor_role`.
- Hash encadeado por registro nao foi adotado por decisao tecnica: exigiria bloqueio
  global serializado em toda escrita de auditoria sem obrigacao normativa; os triggers
  no SGBD e o SHA-256 documental ja garantem append-only (RNF03).
"""

from typing import Sequence, Tuple, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_immutable_audit_and_checks"
down_revision: Union[str, None] = "002_review_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHECK_CONSTRAINTS: Tuple[Tuple[str, str, str], ...] = (
    (
        "documents",
        "ck_documents_status",
        "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'EXTRACTION_FAILED')",
    ),
    (
        "compliance_checks",
        "ck_compliance_checks_status",
        "status IN ('COMPLIANT', 'NON_COMPLIANT', 'MANUAL_REVIEW_REQUIRED', 'NOT_APPLICABLE')",
    ),
    (
        "review_events",
        "ck_review_events_event_type",
        "event_type IN ('PROPOSED', 'CONFIRMED', 'RETURNED')",
    ),
    (
        "review_events",
        "ck_review_events_decision",
        "decision IS NULL OR decision IN ('APPROVE', 'REJECT', 'EXCEPTION')",
    ),
    (
        "review_events",
        "ck_review_events_decision_for_event",
        "(event_type = 'PROPOSED' AND decision IS NOT NULL AND resolves_id IS NULL) OR "
        "(event_type IN ('CONFIRMED', 'RETURNED') AND decision IS NULL AND resolves_id IS NOT NULL)",
    ),
    (
        "review_events",
        "ck_review_events_actor_role",
        "actor_role IN ('ANALISTA', 'AUDITOR', 'ADMIN')",
    ),
)

APPEND_ONLY_TABLES: Tuple[str, ...] = ("audit_logs", "review_events")


def _existing_check_names(bind, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_check_constraints(table_name) if c.get("name")}


def _install_postgres_immutability() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_append_only_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'Tabela % e append-only (RNF03): operacao % nao permitida.',
                TG_TABLE_NAME, TG_OP
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$ LANGUAGE plpgsql;
        """)
    for table in APPEND_ONLY_TABLES:
        trigger_name = f"trg_{table}_immutable"
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table};")
        op.execute(f"""
            CREATE TRIGGER {trigger_name}
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION prevent_append_only_mutation();
            """)


def _drop_postgres_immutability() -> None:
    for table in APPEND_ONLY_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table};")
    op.execute("DROP FUNCTION IF EXISTS prevent_append_only_mutation();")


def _install_sqlite_immutability() -> None:
    for table in APPEND_ONLY_TABLES:
        op.execute(f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN
                SELECT RAISE(ABORT, 'Tabela {table} e append-only (RNF03): UPDATE nao permitido.');
            END;
            """)
        op.execute(f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN
                SELECT RAISE(ABORT, 'Tabela {table} e append-only (RNF03): DELETE nao permitido.');
            END;
            """)


def _drop_sqlite_immutability() -> None:
    for table in APPEND_ONLY_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_no_update;")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_no_delete;")


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1. CHECK constraints de dominio (idempotentes para bancos legados criados via create_all)
    constraints_by_table: dict[str, list[tuple[str, str]]] = {}
    for table, name, condition in CHECK_CONSTRAINTS:
        constraints_by_table.setdefault(table, []).append((name, condition))

    for table, items in constraints_by_table.items():
        existing = _existing_check_names(bind, table)
        missing = [(name, cond) for name, cond in items if name not in existing]
        if not missing:
            continue
        if dialect == "sqlite":
            with op.batch_alter_table(table) as batch_op:
                for name, cond in missing:
                    batch_op.create_check_constraint(name, cond)
        else:
            for name, cond in missing:
                op.create_check_constraint(name, table, cond)

    # 2. Triggers append-only em audit_logs e review_events
    if dialect == "postgresql":
        _install_postgres_immutability()
    elif dialect == "sqlite":
        _install_sqlite_immutability()


def downgrade() -> None:
    # ATENCAO: remove garantias de imutabilidade e restricoes de dominio (RNF03).
    # Executar somente em banco descartavel ou apos backup formal.
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1. Remover triggers antes de alterar tabelas
    if dialect == "postgresql":
        _drop_postgres_immutability()
    elif dialect == "sqlite":
        _drop_sqlite_immutability()

    # 2. Remover CHECK constraints adicionadas nesta revisao
    constraints_by_table: dict[str, list[str]] = {}
    for table, name, _ in CHECK_CONSTRAINTS:
        constraints_by_table.setdefault(table, []).append(name)

    for table, names in constraints_by_table.items():
        existing = _existing_check_names(bind, table)
        present = [name for name in names if name in existing]
        if not present:
            continue
        if dialect == "sqlite":
            with op.batch_alter_table(table) as batch_op:
                for name in present:
                    batch_op.drop_constraint(name, type_="check")
        else:
            for name in present:
                op.drop_constraint(name, table, type_="check")

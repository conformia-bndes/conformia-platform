"""Initial database schema with documents, compliance_checks and audit_logs

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-26 23:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criação da tabela documents
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extracted_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_documents_id", "documents", ["id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    # Criação da tabela compliance_checks
    op.create_table(
        "compliance_checks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=36),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(length=100), nullable=False),
        sa.Column("rule_title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="MANUAL_REVIEW_REQUIRED",
        ),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column(
            "checker_type",
            sa.String(length=50),
            nullable=False,
            server_default="DETERMINISTIC",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_compliance_checks_id", "compliance_checks", ["id"])
    op.create_index("ix_compliance_checks_document_id", "compliance_checks", ["document_id"])
    op.create_index("ix_compliance_checks_rule_id", "compliance_checks", ["rule_id"])
    op.create_index("ix_compliance_checks_status", "compliance_checks", ["status"])

    # Criação da tabela audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column(
            "performed_by",
            sa.String(length=100),
            nullable=False,
            server_default="SYSTEM_HARNESS",
        ),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("compliance_checks")
    op.drop_table("documents")

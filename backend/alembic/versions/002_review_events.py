"""Append-only review_events table for human Maker-Checker review

Revision ID: 002_review_events
Revises: 001_initial_schema
Create Date: 2026-10-29 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_review_events"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=36),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column(
            "resolves_id",
            sa.String(length=36),
            sa.ForeignKey("review_events.id"),
            nullable=True,
            unique=True,
        ),
        sa.Column("report_status", sa.String(length=50), nullable=True),
        sa.Column("actor_id", sa.String(length=100), nullable=False),
        sa.Column("actor_role", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_review_events_document_id", "review_events", ["document_id"])
    op.create_index("ix_review_events_created_at", "review_events", ["created_at"])


def downgrade() -> None:
    # Remove o historico de revisoes: executar somente em banco descartavel ou apos backup.
    op.drop_table("review_events")

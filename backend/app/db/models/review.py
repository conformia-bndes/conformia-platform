"""Append-only human review events (Maker-Checker humano sobre o laudo automatizado)."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.db.session import Base


class ReviewEvent(Base):
    """
    Cada linha e um fato imutavel: uma proposta de decisao (PROPOSED) ou a sua resolucao
    por outro analista (CONFIRMED / RETURNED). Nada e atualizado nem removido; o estado
    atual de uma revisao e derivado dos eventos. `resolves_id` e unico, de modo que uma
    proposta so pode ser resolvida uma vez, mesmo com requisicoes concorrentes.
    """

    __tablename__ = "review_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    # PROPOSED, CONFIRMED, RETURNED
    event_type = Column(String(20), nullable=False)
    # APPROVE, REJECT, EXCEPTION (somente em PROPOSED)
    decision = Column(String(20), nullable=True)
    justification = Column(Text, nullable=False)
    resolves_id = Column(String(36), ForeignKey("review_events.id"), nullable=True, unique=True)
    # Status geral do laudo automatizado no momento da proposta
    report_status = Column(String(50), nullable=True)
    actor_id = Column(String(100), nullable=False)
    actor_role = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

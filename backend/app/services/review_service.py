"""Revisao humana Maker-Checker sobre o laudo automatizado (RF09).

Regras:
- Um analista (Maker) propoe APPROVE, REJECT ou EXCEPTION com justificativa.
- Outro analista (Checker) confirma ou devolve a proposta. O autor da proposta nunca
  resolve a propria proposta (segregacao de funcoes).
- Laudo automatizado NON_COMPLIANT so pode ser aceito como EXCEPTION motivada.
- Eventos sao append-only; cada um gera tambem um registro na trilha de auditoria.

As funcoes nao fazem commit: o chamador controla a transacao.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.security import Principal
from app.db.models.compliance import AuditLog, ComplianceCheck
from app.db.models.document import Document
from app.db.models.review import ReviewEvent
from app.services.rules_engine import summarize_statuses


class ReviewError(Exception):
    """Violacao de regra da revisao; `status_code` orienta a traducao para HTTP."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ReviewNotFound(ReviewError):
    status_code = 404


class ReviewForbidden(ReviewError):
    status_code = 403


class ReviewConflict(ReviewError):
    status_code = 409


class ReviewInvalid(ReviewError):
    status_code = 422


def _load_document(db: Session, document_id: str, lock: bool = False) -> Document:
    query = db.query(Document).filter(Document.id == document_id)
    if lock:
        # Serializa propostas concorrentes no PostgreSQL (no-op no SQLite de testes).
        query = query.with_for_update()
    doc = query.first()
    if doc is None:
        raise ReviewNotFound("Documento nao encontrado.")
    return doc


def _events(db: Session, document_id: str) -> List[ReviewEvent]:
    return (
        db.query(ReviewEvent)
        .filter(ReviewEvent.document_id == document_id)
        .order_by(ReviewEvent.created_at)
        .all()
    )


def _next_timestamp(db: Session, document_id: str) -> datetime:
    """
    Timestamp estritamente crescente por documento: o estado da revisao e derivado da
    ordem dos eventos, que nao pode empatar mesmo com duas acoes no mesmo instante.
    """
    now = datetime.utcnow()
    last = (
        db.query(ReviewEvent.created_at)
        .filter(ReviewEvent.document_id == document_id)
        .order_by(ReviewEvent.created_at.desc())
        .first()
    )
    if last is not None and now <= last[0]:
        return last[0] + timedelta(microseconds=1)
    return now


def _pending_proposal(events: List[ReviewEvent]) -> Optional[ReviewEvent]:
    resolved = {e.resolves_id for e in events if e.resolves_id}
    pending = [e for e in events if e.event_type == "PROPOSED" and e.id not in resolved]
    return pending[-1] if pending else None


def get_review_state(db: Session, document_id: str) -> Dict[str, Any]:
    _load_document(db, document_id)
    events = _events(db, document_id)
    pending = _pending_proposal(events)
    proposals = {e.id: e for e in events if e.event_type == "PROPOSED"}
    resolutions = [e for e in events if e.event_type in ("CONFIRMED", "RETURNED")]
    confirmed = [e for e in resolutions if e.event_type == "CONFIRMED"]

    if pending is not None:
        state = "PENDING_CHECK"
    elif not resolutions:
        state = "NO_REVIEW"
    else:
        state = "FINAL" if resolutions[-1].event_type == "CONFIRMED" else "RETURNED"

    return {
        "document_id": document_id,
        "state": state,
        "final_decision": proposals[confirmed[-1].resolves_id].decision if confirmed else None,
        "pending_proposal_id": pending.id if pending else None,
        "events": events,
    }


def propose_decision(
    db: Session, document_id: str, decision: str, justification: str, principal: Principal
) -> ReviewEvent:
    _load_document(db, document_id, lock=True)

    statuses = [
        status
        for (status,) in db.query(ComplianceCheck.status).filter(
            ComplianceCheck.document_id == document_id
        )
    ]
    if not statuses:
        raise ReviewConflict("Documento sem laudo de conformidade; execute a verificacao antes.")
    report_status, _ = summarize_statuses(statuses)

    if report_status == "NON_COMPLIANT" and decision == "APPROVE":
        raise ReviewInvalid(
            "Laudo NON_COMPLIANT nao pode ser aprovado diretamente; "
            "use EXCEPTION com justificativa tecnica."
        )
    if _pending_proposal(_events(db, document_id)) is not None:
        raise ReviewConflict("Ja existe proposta aguardando revisao para este documento.")

    event = ReviewEvent(
        document_id=document_id,
        event_type="PROPOSED",
        decision=decision,
        justification=justification,
        report_status=report_status,
        actor_id=principal.user_id,
        actor_role=principal.role,
        created_at=_next_timestamp(db, document_id),
    )
    db.add(event)
    db.flush()
    _audit(db, event, "REVIEW_PROPOSED")
    return event


def resolve_proposal(
    db: Session,
    document_id: str,
    proposal_id: str,
    outcome: str,
    comment: str,
    principal: Principal,
) -> ReviewEvent:
    _load_document(db, document_id)
    proposal = (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.id == proposal_id,
            ReviewEvent.document_id == document_id,
            ReviewEvent.event_type == "PROPOSED",
        )
        .first()
    )
    if proposal is None:
        raise ReviewNotFound("Proposta de revisao nao encontrada para este documento.")
    if proposal.actor_id == principal.user_id:
        raise ReviewForbidden(
            "Segregacao de funcoes: o autor da proposta nao pode confirma-la nem devolve-la."
        )
    if db.query(ReviewEvent).filter(ReviewEvent.resolves_id == proposal_id).first():
        raise ReviewConflict("Proposta ja resolvida.")

    event = ReviewEvent(
        document_id=document_id,
        event_type=outcome,
        justification=comment,
        resolves_id=proposal_id,
        report_status=proposal.report_status,
        actor_id=principal.user_id,
        actor_role=principal.role,
        created_at=_next_timestamp(db, document_id),
    )
    db.add(event)
    db.flush()
    _audit(db, event, f"REVIEW_{outcome}", decision=proposal.decision)
    return event


def _audit(db: Session, event: ReviewEvent, action: str, decision: Optional[str] = None) -> None:
    db.add(
        AuditLog(
            entity_type="DOCUMENT",
            entity_id=event.document_id,
            action=action,
            performed_by=event.actor_id,
            details={
                "review_event_id": event.id,
                "proposal_id": event.resolves_id or event.id,
                "decision": event.decision or decision,
                "report_status": event.report_status,
                "actor_role": event.actor_role,
            },
        )
    )

"""Avaliacao de conformidade de um documento e persistencia do laudo e da auditoria.

Ponto unico usado pelo worker Celery e pela API, para que ambos apliquem as mesmas
regras, o mesmo filtro de tipologia e o mesmo formato de laudo.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models.compliance import AuditLog, ComplianceCheck
from app.db.models.document import Document
from app.idp.parser import extract_fields_and_evidence
from app.services.review_service import ReviewConflict, get_review_state
from app.services.rules_engine import RulesEngine

UNIDENTIFIED_TYPE_REASON = (
    "Tipologia documental nao identificada no texto extraido. "
    "Nenhuma regra foi aplicada; necessita revisao manual por analista BNDES."
)


def resolve_document_type(doc: Document) -> Optional[str]:
    """Tipologia gravada pela extracao; se ausente, e detectada novamente a partir do texto."""
    metadata = doc.extracted_metadata if isinstance(doc.extracted_metadata, dict) else {}
    extraction = metadata.get("extraction")
    if isinstance(extraction, dict) and extraction.get("document_type"):
        return extraction["document_type"]
    return extract_fields_and_evidence(
        doc.extracted_text or "", pages=metadata.get("pages")
    ).document_type


def _resolve_evaluation_actor(
    db: Session,
    document_id: str,
    performed_by: str,
    actor_role: Optional[str] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Resolve o executor real da avaliacao para a trilha de auditoria (RF10 / Issue #163).
    Quando acionada pelo worker assincrono (`CELERY_WORKER`), propaga o autor gravado no
    evento `DOCUMENT_UPLOADED` daquele documento e registra `trigger="CELERY_WORKER"`.
    """
    if performed_by != "CELERY_WORKER":
        return performed_by, actor_role, None

    upload_audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == "DOCUMENT",
            AuditLog.entity_id == document_id,
            AuditLog.action == "DOCUMENT_UPLOADED",
        )
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    if upload_audit and upload_audit.performed_by:
        upload_role = (
            upload_audit.details.get("actor_role")
            if isinstance(upload_audit.details, dict)
            else None
        )
        return upload_audit.performed_by, upload_role, "CELERY_WORKER"
    return performed_by, actor_role, "CELERY_WORKER"


def evaluate_and_persist(
    db: Session,
    doc: Document,
    performed_by: str,
    engine: Optional[RulesEngine] = None,
    actor_role: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[ComplianceCheck]]:
    """
    Avalia o documento, substitui o laudo vigente e registra a avaliacao na trilha de
    auditoria. Nao faz commit: o chamador controla a transacao, de modo que laudo e
    auditoria sao gravados juntos ou nao sao gravados.
    """
    review_state = get_review_state(db, doc.id)["state"]
    if review_state in ("PENDING_CHECK", "FINAL"):
        raise ReviewConflict(
            f"Reavaliacao bloqueada: documento possui revisao humana em estado {review_state}."
        )

    engine = engine or RulesEngine()
    document_type = resolve_document_type(doc)
    if document_type is None:
        evaluation = engine.not_evaluable(UNIDENTIFIED_TYPE_REASON)
    else:
        evaluation = engine.evaluate(
            {"full_text": doc.extracted_text or "", "metadata": doc.extracted_metadata or {}},
            document_type=document_type,
        )

    # O laudo vigente e substituido (reprocessamentos e retries nao duplicam checagens);
    # o historico de cada avaliacao permanece na trilha de auditoria append-only.
    db.query(ComplianceCheck).filter(ComplianceCheck.document_id == doc.id).delete()

    checks = [
        ComplianceCheck(
            document_id=doc.id,
            rule_id=result["rule_id"],
            rule_title=result["rule_title"],
            category=result["category"],
            status=result["status"],
            confidence_score=result.get("confidence_score", 1.0),
            checker_type=result.get("checker_type", "DETERMINISTIC"),
            findings=result.get("findings"),
            evidence=result.get("evidence"),
        )
        for result in evaluation["results"]
    ]
    db.add_all(checks)

    resolved_actor, resolved_role, trigger = _resolve_evaluation_actor(
        db, doc.id, performed_by, actor_role=actor_role
    )
    audit_details: Dict[str, Any] = {
        "overall_status": evaluation["overall_status"],
        "document_type": document_type,
        "compliance_score": evaluation["compliance_score"],
        "total_rules": evaluation["total_rules"],
        "evaluated_rules": evaluation["evaluated_rules"],
        "compliant_rules": evaluation["compliant_rules"],
    }
    if resolved_role:
        audit_details["actor_role"] = resolved_role
    if trigger:
        audit_details["trigger"] = trigger

    db.add(
        AuditLog(
            entity_type="DOCUMENT",
            entity_id=doc.id,
            action="COMPLIANCE_EVALUATION",
            performed_by=resolved_actor,
            details=audit_details,
        )
    )
    return evaluation, checks

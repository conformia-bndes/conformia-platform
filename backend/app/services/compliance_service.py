"""Avaliacao de conformidade de um documento e persistencia do laudo e da auditoria.

Ponto unico usado pelo worker Celery e pela API, para que ambos apliquem as mesmas
regras, o mesmo filtro de tipologia e o mesmo formato de laudo.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models.compliance import AuditLog, ComplianceCheck
from app.db.models.document import Document
from app.idp.parser import extract_fields_and_evidence
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


def evaluate_and_persist(
    db: Session,
    doc: Document,
    performed_by: str,
    engine: Optional[RulesEngine] = None,
) -> Tuple[Dict[str, Any], List[ComplianceCheck]]:
    """
    Avalia o documento, substitui o laudo vigente e registra a avaliacao na trilha de
    auditoria. Nao faz commit: o chamador controla a transacao, de modo que laudo e
    auditoria sao gravados juntos ou nao sao gravados.
    """
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

    db.add(
        AuditLog(
            entity_type="DOCUMENT",
            entity_id=doc.id,
            action="COMPLIANCE_EVALUATION",
            performed_by=performed_by,
            details={
                "overall_status": evaluation["overall_status"],
                "document_type": document_type,
                "compliance_score": evaluation["compliance_score"],
                "total_rules": evaluation["total_rules"],
                "evaluated_rules": evaluation["evaluated_rules"],
                "compliant_rules": evaluation["compliant_rules"],
            },
        )
    )
    return evaluation, checks

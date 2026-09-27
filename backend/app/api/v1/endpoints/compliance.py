"""Compliance verification, rules management and audit trail endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.db.models.compliance import ComplianceCheck, AuditLog
from app.services.rules_engine import RulesEngine

router = APIRouter()


@router.post("/verify/{document_id}", summary="Disparar Verificação de Conformidade Documental")
def verify_document_compliance(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Executa o motor de regras determinísticas e orquestração Maker-Checker no texto do documento,
    gerando o laudo de conformidade e registrando a trilha de auditoria imutável.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    if not doc.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O documento selecionado não possui texto extraído para validação."
        )

    engine = RulesEngine()
    evaluation = engine.evaluate({
        "full_text": doc.extracted_text,
        "metadata": doc.extracted_metadata or {}
    })

    # Limpa checagens anteriores do mesmo documento para idempotência
    db.query(ComplianceCheck).filter(ComplianceCheck.document_id == document_id).delete()

    saved_checks = []
    for res in evaluation.get("results", []):
        check = ComplianceCheck(
            document_id=doc.id,
            rule_id=res["rule_id"],
            rule_title=res["rule_title"],
            category=res["category"],
            status=res["status"],
            confidence_score=res.get("confidence_score", 1.0),
            checker_type=res.get("checker_type", "DETERMINISTIC"),
            findings=res.get("findings"),
            evidence=res.get("evidence")
        )
        db.add(check)
        saved_checks.append(check)

    # Gravação na trilha de auditoria
    audit_entry = AuditLog(
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="COMPLIANCE_VERIFIED",
        performed_by="HARNESS_RULES_ENGINE",
        details={
            "status": evaluation.get("status"),
            "compliance_score": evaluation.get("compliance_score"),
            "total_rules": evaluation.get("total_rules"),
            "compliant_rules": evaluation.get("compliant_rules")
        }
    )
    db.add(audit_entry)
    db.commit()

    return {
        "document_id": doc.id,
        "document_filename": doc.original_filename,
        "overall_status": evaluation.get("status"),
        "compliance_score": evaluation.get("compliance_score"),
        "total_rules": evaluation.get("total_rules"),
        "compliant_rules": evaluation.get("compliant_rules"),
        "checks": [
            {
                "rule_id": c.rule_id,
                "rule_title": c.rule_title,
                "category": c.category,
                "status": c.status,
                "confidence_score": c.confidence_score,
                "checker_type": c.checker_type,
                "findings": c.findings
            }
            for c in saved_checks
        ]
    }


@router.get("/rules", summary="Consultar Checklist e Regras Ativas de Conformidade")
def get_active_rules():
    """Retorna o catálogo de regras ativas configuradas no motor de conformidade."""
    engine = RulesEngine()
    return {
        "total_rules": len(engine.rules),
        "rules": engine.rules
    }


@router.get("/results/{document_id}", summary="Obter Relatório de Conformidade de um Documento")
def get_compliance_results(document_id: str, db: Session = Depends(get_db)):
    """Retorna os resultados da última verificação de conformidade do documento."""
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.document_id == document_id).all()
    if not checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma verificação de conformidade encontrada para este documento."
        )

    compliant_count = sum(1 for c in checks if c.status == "COMPLIANT")
    total = len(checks)
    score = (compliant_count / total) if total > 0 else 0.0

    return {
        "document_id": document_id,
        "total_rules": total,
        "compliant_rules": compliant_count,
        "compliance_score": round(score, 2),
        "checks": [
            {
                "rule_id": c.rule_id,
                "rule_title": c.rule_title,
                "category": c.category,
                "status": c.status,
                "confidence_score": c.confidence_score,
                "checker_type": c.checker_type,
                "findings": c.findings,
                "evidence": c.evidence
            }
            for c in checks
        ]
    }


@router.get("/audit-trail", summary="Consultar Trilha de Auditoria Imutável")
def get_audit_trail(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Retorna registros de auditoria em ordem cronológica reversa."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(AuditLog).count()
    return {
        "total": total,
        "items": [
            {
                "id": l.id,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "action": l.action,
                "performed_by": l.performed_by,
                "details": l.details,
                "timestamp": l.created_at.isoformat()
            }
            for l in logs
        ]
    }

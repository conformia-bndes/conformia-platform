from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.db.models.compliance import ComplianceCheck, AuditLog
from app.services.compliance_service import evaluate_and_persist
from app.services.rules_engine import RulesEngine, summarize_statuses

router = APIRouter()


@router.post("/verify/{document_id}", summary="Disparar Verificação de Conformidade Documental")
def verify_document_compliance(document_id: str, db: Session = Depends(get_db)):
    """
    Executa o motor de regras determinísticas e orquestração Maker-Checker no texto do documento,
    gerando o laudo de conformidade e registrando a trilha de auditoria imutável.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado."
        )

    if not doc.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O documento selecionado não possui texto extraído para validação.",
        )

    evaluation, saved_checks = evaluate_and_persist(db, doc, performed_by="HARNESS_RULES_ENGINE")
    db.commit()

    return {
        "document_id": doc.id,
        "document_filename": doc.original_filename,
        "document_type": evaluation["document_type"],
        "overall_status": evaluation["overall_status"],
        "compliance_score": evaluation["compliance_score"],
        "total_rules": evaluation["total_rules"],
        "evaluated_rules": evaluation["evaluated_rules"],
        "compliant_rules": evaluation["compliant_rules"],
        "checks": [
            {
                "rule_id": c.rule_id,
                "rule_title": c.rule_title,
                "category": c.category,
                "status": c.status,
                "confidence_score": c.confidence_score,
                "checker_type": c.checker_type,
                "findings": c.findings,
                "evidence": c.evidence,
            }
            for c in saved_checks
        ],
    }


@router.get("/rules", summary="Consultar Checklist e Regras Ativas de Conformidade")
def get_active_rules():
    """Retorna o catálogo de regras ativas configuradas no motor de conformidade."""
    engine = RulesEngine()
    return {"total_rules": len(engine.rules), "rules": engine.rules}


@router.get("/results/{document_id}", summary="Obter Relatório de Conformidade de um Documento")
def get_compliance_results(document_id: str, db: Session = Depends(get_db)):
    """Retorna os resultados da última verificação de conformidade do documento."""
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.document_id == document_id).all()
    if not checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma verificação de conformidade encontrada para este documento.",
        )

    overall_status, score = summarize_statuses([c.status for c in checks])

    return {
        "document_id": document_id,
        "overall_status": overall_status,
        "total_rules": len(checks),
        "evaluated_rules": sum(1 for c in checks if c.status != "NOT_APPLICABLE"),
        "compliant_rules": sum(1 for c in checks if c.status == "COMPLIANT"),
        "compliance_score": score,
        "checks": [
            {
                "rule_id": c.rule_id,
                "rule_title": c.rule_title,
                "category": c.category,
                "status": c.status,
                "confidence_score": c.confidence_score,
                "checker_type": c.checker_type,
                "findings": c.findings,
                "evidence": c.evidence,
            }
            for c in checks
        ],
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
                "id": log_item.id,
                "entity_type": log_item.entity_type,
                "entity_id": log_item.entity_id,
                "action": log_item.action,
                "performed_by": log_item.performed_by,
                "details": log_item.details,
                "timestamp": log_item.created_at.isoformat(),
            }
            for log_item in logs
        ],
    }

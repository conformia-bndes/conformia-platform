"""Celery application configuration and task queue definition."""

import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

celery = Celery(
    "conformia_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutos máximo por documento
)


@celery.task(bind=True, name="app.idp.tasks.process_document")
def process_document_task(self, document_id: str, file_path: str, object_name: str = None):
    """
    Tarefa assincrona para extracao IDP e verificacao de conformidade documental.
    """
    logger.info(f"Iniciando processamento IDP do documento {document_id} a partir de {file_path}")
    from app.db.session import SessionLocal
    from app.db.models.document import Document
    from app.db.models.compliance import ComplianceCheck, AuditLog
    from app.idp.extractor import DocumentExtractor
    from app.services.rules_engine import RulesEngine
    from app.core.storage import storage_service
    import os

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Documento {document_id} nao encontrado no banco de dados.")
            return {"error": "Document not found"}

        doc.status = "PROCESSING"
        db.commit()

        # Baixar do MinIO se nao existir localmente
        if not os.path.exists(file_path) and object_name:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            storage_service.download_file(object_name, file_path)

        extractor = DocumentExtractor()
        extracted_data = extractor.extract(file_path)

        doc.extracted_text = extracted_data.get("full_text")
        doc.extracted_metadata = extracted_data.get("metadata")

        engine = RulesEngine()
        compliance_results = engine.evaluate(extracted_data)

        # Persistir resultados de conformidade individuais
        for check in compliance_results.get("checks", []):
            compliance_check = ComplianceCheck(
                document_id=doc.id,
                rule_id=check["rule_id"],
                rule_title=check["rule_title"],
                category=check["category"],
                status=check["status"],
                confidence_score=check.get("confidence_score", 1.0),
                evidence=check.get("evidence", {}),
                findings=check.get("findings", ""),
                checker_type=check.get("checker_type", "DETERMINISTIC"),
            )
            db.add(compliance_check)

        # Registrar log de auditoria imutavel
        audit = AuditLog(
            entity_type="DOCUMENT",
            entity_id=doc.id,
            action="COMPLIANCE_EVALUATION",
            performed_by="CELERY_WORKER",
            details={
                "overall_status": compliance_results.get("overall_status"),
                "total_rules": compliance_results.get("total_rules"),
                "compliance_score": compliance_results.get("compliance_score"),
            },
        )
        db.add(audit)

        doc.status = "COMPLETED"
        db.commit()

        logger.info(
            f"Processamento concluido para {document_id}. "
            f"Status: {compliance_results.get('overall_status')}"
        )
        return {
            "document_id": document_id,
            "status": "COMPLETED",
            "compliance_summary": compliance_results,
        }
    except Exception as exc:
        db.rollback()
        logger.error(f"Erro ao processar documento {document_id}: {str(exc)}", exc_info=True)
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "EXTRACTION_FAILED"
                doc.extracted_metadata = {"error": str(exc)}
                db.commit()
        except Exception:
            pass
        self.retry(exc=exc, countdown=10, max_retries=3)
    finally:
        db.close()

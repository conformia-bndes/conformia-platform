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
    from app.idp.extractor import DocumentExtractor
    from app.services.compliance_service import evaluate_and_persist
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
        extracted_data = extractor.extract(file_path, document_id=document_id)
        doc.extracted_text = extracted_data.get("full_text")
        doc_metadata = extracted_data.get("metadata") or {}

        from app.idp.parser import extract_fields_and_evidence

        extraction_result = extract_fields_and_evidence(
            text=doc.extracted_text or "",
            pages=extracted_data.get("pages"),
        )
        doc_metadata["pages"] = extracted_data.get("pages", [])
        doc_metadata["extraction"] = extraction_result.model_dump()
        doc.extracted_metadata = doc_metadata

        # Laudo, auditoria e status COMPLETED sao gravados no mesmo commit.
        compliance_results, _ = evaluate_and_persist(db, doc, performed_by="CELERY_WORKER")

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
                doc.extracted_metadata = {
                    "error": str(exc),
                    "error_detail": {
                        "code": "EXTRACTION_FAILED",
                        "message": str(exc),
                        "details": {"stage": "celery_worker_idp"},
                    },
                }
                db.commit()
        except Exception:
            logger.exception(f"Falha ao registrar EXTRACTION_FAILED para {document_id}")
        self.retry(exc=exc, countdown=10, max_retries=3)
    finally:
        db.close()

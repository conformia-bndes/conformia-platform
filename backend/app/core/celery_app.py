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
def process_document_task(self, document_id: str, file_path: str):
    """
    Tarefa assíncrona para extração de texto/tabelas e verificação de conformidade documental.
    """
    logger.info(f"Iniciando processamento IDP do documento {document_id} a partir de {file_path}")
    try:
        from app.idp.extractor import DocumentExtractor
        from app.services.rules_engine import RulesEngine

        extractor = DocumentExtractor()
        extracted_data = extractor.extract(file_path)

        engine = RulesEngine()
        compliance_results = engine.evaluate(extracted_data)

        logger.info(f"Processamento concluído para {document_id}. Status: {compliance_results.get('status')}")
        return {
            "document_id": document_id,
            "status": "COMPLETED",
            "extracted_metadata": extracted_data.get("metadata"),
            "compliance_summary": compliance_results,
        }
    except Exception as exc:
        logger.error(f"Erro ao processar documento {document_id}: {str(exc)}", exc_info=True)
        self.retry(exc=exc, countdown=10, max_retries=3)

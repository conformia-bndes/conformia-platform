"""Celery application configuration and task queue definition."""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/conformia_uploads")


def _get_upload_root() -> Path:
    """Retorna o diretorio base de uploads normalizado."""
    return Path(os.path.abspath(os.getenv("UPLOAD_DIR", UPLOAD_DIR))).resolve()


def _validate_document_id(document_id: str) -> str:
    """Garante que document_id e um identificador simples sem separadores ou traversal."""
    if (
        not isinstance(document_id, str)
        or not document_id.strip()
        or ".." in document_id
        or "/" in document_id
        or "\\" in document_id
        or os.path.basename(document_id) != document_id
    ):
        raise ValueError(f"document_id invalido para processamento: {document_id!r}")
    return document_id


def _belongs_to_document(filename: str, document_id: str) -> bool:
    """Nome gerado pelo upload: '<document_id>_<nome>' (ou '<document_id>.pdf')."""
    return filename.startswith(f"{document_id}_") or filename == f"{document_id}.pdf"


def _validate_and_resolve_task_paths(
    document_id: str,
    file_path: Optional[str] = None,
    doc_filename: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Valida e deriva (file_path, object_name) dentro de UPLOAD_DIR a partir de document_id.

    - Rejeita qualquer file_path com '..' ou que resolva fora de UPLOAD_DIR.
    - Rejeita nomes de arquivo que nao pertencam ao document_id informado.
    - Deriva object_name exclusivamente do registro do documento (ou do nome validado),
      nunca confiando no argumento object_name vindo do broker.
    """
    safe_doc_id = _validate_document_id(document_id)
    upload_root = _get_upload_root()

    derived_name: Optional[str] = None
    if doc_filename:
        base_doc_name = os.path.basename(doc_filename)
        if (
            base_doc_name != doc_filename
            or ".." in base_doc_name
            or not _belongs_to_document(base_doc_name, safe_doc_id)
        ):
            raise ValueError(
                f"Nome de arquivo do documento invalido para {safe_doc_id}: {doc_filename!r}"
            )
        derived_name = base_doc_name

    if file_path is not None:
        raw_path = str(file_path).strip()
        if not raw_path or ".." in Path(raw_path).parts:
            raise ValueError(f"file_path invalido ou fora de UPLOAD_DIR: {file_path!r}")
        if os.path.isabs(raw_path) or raw_path.startswith(("/", "\\")):
            candidate = Path(os.path.abspath(raw_path)).resolve()
        else:
            candidate = (upload_root / raw_path).resolve()

        if candidate == upload_root or candidate.parent != upload_root:
            raise ValueError(f"file_path fora de UPLOAD_DIR rejeitado: {file_path!r}")
        if not _belongs_to_document(candidate.name, safe_doc_id):
            raise ValueError(
                f"file_path ({candidate.name!r}) nao corresponde ao document_id ({safe_doc_id!r})"
            )
        if derived_name is None:
            derived_name = candidate.name
    else:
        if derived_name is None:
            derived_name = f"{safe_doc_id}.pdf"
        candidate = (upload_root / derived_name).resolve()
        if candidate.parent != upload_root:
            raise ValueError(f"Caminho derivado fora de UPLOAD_DIR: {candidate}")

    # Se o documento existe no banco, o caminho local e o object_name seguem o nome derivado.
    safe_target = (upload_root / derived_name).resolve()
    if safe_target.parent != upload_root:
        raise ValueError(f"Caminho final fora de UPLOAD_DIR: {safe_target}")

    return str(safe_target), derived_name


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
    worker_concurrency=settings.CELERY_CONCURRENCY,
    # Com o Redis fora do ar, o publicador reconectava indefinidamente e o upload travava por
    # minutos. Falhar rapido deixa a API responder 503; o worker continua reconectando ao
    # broker por conta propria.
    broker_connection_timeout=2,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"socket_connect_timeout": 2},
    # O backend de resultados (tambem Redis) tem politica de reconexao propria.
    redis_socket_connect_timeout=2,
    redis_socket_timeout=5,
    result_backend_always_retry=False,
    result_backend_transport_options={
        "retry_policy": {"max_retries": 1, "interval_start": 0, "interval_step": 0.2}
    },
    task_publish_retry=True,
    task_publish_retry_policy={
        "max_retries": 1,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
)


@celery.task(bind=True, name="app.idp.tasks.process_document")
def process_document_task(
    self, document_id: str, file_path: Optional[str] = None, object_name: Optional[str] = None
):
    """
    Tarefa assincrona para extracao IDP e verificacao de conformidade documental.

    Por seguranca (Issue #164), `file_path` e validado/derivado de `document_id` estritamente
    dentro de `UPLOAD_DIR`, e `object_name` recebido pelo broker nao e confiado (derivado do
    registro persistido do documento).
    """
    # Valida os argumentos antes de qualquer acesso a disco ou storage externo.
    validated_path, _ = _validate_and_resolve_task_paths(document_id, file_path)
    logger.info(
        f"Iniciando processamento IDP do documento {document_id} a partir de {validated_path}"
    )
    from app.db.session import SessionLocal
    from app.db.models.document import Document
    from app.idp.extractor import DocumentExtractor
    from app.services.compliance_service import evaluate_and_persist
    from app.core.storage import storage_service

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Documento {document_id} nao encontrado no banco de dados.")
            return {"error": "Document not found"}

        safe_file_path, safe_object_name = _validate_and_resolve_task_paths(
            document_id, file_path, doc_filename=doc.filename
        )

        doc.status = "PROCESSING"
        db.commit()

        # Baixar do MinIO se nao existir localmente (usando apenas object_name e caminho derivados)
        if not os.path.exists(safe_file_path) and safe_object_name:
            os.makedirs(os.path.dirname(safe_file_path), exist_ok=True)
            storage_service.download_file(safe_object_name, safe_file_path)

        extractor = DocumentExtractor()
        extracted_data = extractor.extract(safe_file_path, document_id=document_id)
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

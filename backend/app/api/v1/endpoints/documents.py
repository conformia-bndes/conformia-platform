"""Document ingestion and retrieval endpoints with MinIO storage and Celery tasks."""

import logging
import os
import uuid
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.core.storage import storage_service
from app.core.celery_app import celery, process_document_task
from app.idp.extractor import DocumentExtractor

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/conformia_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload de Documento PDF para Ingestao",
)
def upload_document(
    file: UploadFile = File(...),
    async_process: bool = Query(
        True,
        description=(
            "Despacha o processamento ao worker Celery (padrao) e retorna 'task_id'. "
            "Use false apenas para depuracao: executa a extracao dentro da requisicao."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Recebe um arquivo PDF, valida assinatura binaria (%PDF-), persiste no MinIO
    e despacha o processamento IDP ao worker via Celery (ou executa inline com
    async_process=false). O estado pode ser consultado em GET /documents/{id} ou
    GET /documents/tasks/{task_id}.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos no formato PDF sao suportados pelo Conform.IA BNDES.",
        )

    # Validacao de tamanho e assinatura binaria (magic bytes)
    try:
        content = file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falha ao ler conteudo do arquivo: {str(e)}",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite maximo de {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo fornecido nao possui assinatura binaria valida de PDF (%PDF-).",
        )

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{os.path.basename(file.filename)}"
    destination_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Gravacao local para processamento imediato
    try:
        with open(destination_path, "wb") as buffer:
            buffer.write(content)
        file_size = len(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gravar arquivo em disco: {str(e)}",
        )

    # Upload para o MinIO / S3 com fallback para armazenamento local
    storage_path = destination_path
    try:
        storage_path = storage_service.upload_file(
            file_data=content,
            object_name=safe_filename,
            content_type=file.content_type or "application/pdf",
        )
    except Exception as storage_err:
        if async_process:
            # O worker roda em outro container e so enxerga o arquivo via MinIO.
            os.remove(destination_path)
            logger.error(f"Falha no upload para o MinIO: {str(storage_err)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Armazenamento de objetos (MinIO) indisponivel. Tente novamente.",
            )
        logger.warning(
            f"Falha no upload para o MinIO: {str(storage_err)}. "
            f"Mantendo copia local em {destination_path}"
        )

    # Criacao do registro no banco
    doc = Document(
        id=doc_id,
        filename=safe_filename,
        original_filename=file.filename,
        content_type=file.content_type or "application/pdf",
        file_size=file_size,
        storage_path=storage_path,
        status="PROCESSING" if async_process else "PENDING",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    task_id = None
    if async_process:
        try:
            task_id = process_document_task.delay(doc.id, destination_path, safe_filename).id
        except Exception as task_err:
            # Sem fallback silencioso: um broker fora do ar deve aparecer como erro,
            # e nao como "sucesso" processado fora da fila.
            logger.error(f"Falha ao despachar tarefa ao Celery: {str(task_err)}")
            doc.status = "EXTRACTION_FAILED"
            doc.extracted_metadata = {"error": "Fila de processamento indisponivel."}
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Fila de processamento (Redis/Celery) indisponivel.",
            )
    else:
        try:
            extractor = DocumentExtractor()
            extracted = extractor.extract(destination_path)
            doc.extracted_text = extracted.get("full_text")
            doc.extracted_metadata = extracted.get("metadata")
            doc.status = "COMPLETED"
        except Exception as ex:
            doc.status = "EXTRACTION_FAILED"
            doc.extracted_metadata = {"error": str(ex)}
        db.commit()
        db.refresh(doc)

    return {
        "id": doc.id,
        "task_id": task_id,
        "filename": doc.original_filename,
        "status": doc.status,
        "file_size": doc.file_size,
        "total_pages": (doc.extracted_metadata.get("total_pages") if doc.extracted_metadata else 0),
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/tasks/{task_id}", summary="Consultar Estado de uma Tarefa de Processamento")
def get_task_status(task_id: str):
    """
    Retorna o estado Celery da tarefa: PENDING, STARTED, RETRY, SUCCESS ou FAILURE.

    Atencao: o Celery nao diferencia um id inexistente de uma tarefa ainda na fila
    (ambos aparecem como PENDING). Use o task_id devolvido pelo upload.
    """
    try:
        result = AsyncResult(task_id, app=celery)
        state = result.state
        payload = {"task_id": task_id, "state": state}
        if state == "SUCCESS" and isinstance(result.result, dict):
            summary = result.result.get("compliance_summary") or {}
            payload["result"] = {
                "document_id": result.result.get("document_id"),
                "status": result.result.get("status"),
                "overall_status": summary.get("overall_status"),
                "compliance_score": summary.get("compliance_score"),
            }
        elif state in ("FAILURE", "RETRY"):
            payload["error"] = str(result.result)
        return payload
    except Exception as exc:
        logger.error(f"Falha ao consultar backend de resultados: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend de resultados (Redis) indisponivel.",
        )


@router.get("", summary="Listar Documentos Ingeridos")
def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Retorna lista paginada de documentos processados."""
    docs = db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Document).count()
    return {
        "total": total,
        "items": [
            {
                "id": d.id,
                "original_filename": d.original_filename,
                "status": d.status,
                "file_size": d.file_size,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "total_pages": (
                    d.extracted_metadata.get("total_pages") if d.extracted_metadata else 0
                ),
            }
            for d in docs
        ],
    }


@router.get("/{document_id}", summary="Obter Detalhes do Documento e Texto Extraido")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retorna dados detalhados do documento pelo identificador unico."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        )

    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "status": doc.status,
        "file_size": doc.file_size,
        "storage_path": doc.storage_path,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "metadata": doc.extracted_metadata,
        "extracted_text_preview": (
            (doc.extracted_text[:1000] + "...") if doc.extracted_text else ""
        ),
    }

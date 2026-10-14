"""Document ingestion, status query and retrieval endpoints with MinIO and Celery."""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.celery_app import process_document_task
from app.core.storage import storage_service
from app.db.models.document import Document
from app.db.session import get_db
from app.idp.extractor import DocumentExtractor
from app.idp.parser import (
    build_processing_status_response,
    extract_fields_and_evidence,
)
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.schemas.enums import ProcessingStatus
from app.schemas.error import ErrorResponse
from app.schemas.processing import ProcessingStatusResponse

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/conformia_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

PROCESSING_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "sucesso": {
        "summary": "Processamento concluido com sucesso",
        "description": "Documento processado com payload e evidencias textuais e de pagina.",
        "value": {
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "cnd_receita_federal.pdf",
            "status": "COMPLETED",
            "progress": 1.0,
            "message": "Processamento e extracao concluidos com sucesso.",
            "extraction": {
                "document_type": "CND_FEDERAL",
                "fields": {
                    "cnpj": {
                        "name": "cnpj",
                        "value": "12.345.678/0001-90",
                        "raw_value": "12.345.678/0001-90",
                        "confidence": 1.0,
                        "evidence": {
                            "text": "CNPJ: 12.345.678/0001-90",
                            "page": 1,
                            "confidence": 1.0,
                            "bounding_box": None,
                        },
                    },
                    "data_validade": {
                        "name": "data_validade",
                        "value": "2026-12-31",
                        "raw_value": "31/12/2026",
                        "confidence": 1.0,
                        "evidence": {
                            "text": "Valida ate: 31/12/2026",
                            "page": 1,
                            "confidence": 1.0,
                            "bounding_box": None,
                        },
                    },
                },
                "evidences": [
                    {
                        "text": "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
                        "page": 1,
                        "confidence": 1.0,
                        "bounding_box": None,
                    },
                    {
                        "text": "CNPJ: 12.345.678/0001-90",
                        "page": 1,
                        "confidence": 1.0,
                        "bounding_box": None,
                    },
                ],
                "total_pages": 1,
                "tables": [],
                "full_text_preview": "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA...",
            },
            "error": None,
            "created_at": "2026-10-12T19:00:00Z",
            "updated_at": "2026-10-12T19:00:05Z",
        },
    },
    "em_processamento": {
        "summary": "Documento em processamento",
        "description": "Documento em fila ou em execucao na esteira IDP e OCR.",
        "value": {
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "certidao_fgts_crf.pdf",
            "status": "PROCESSING",
            "progress": 0.5,
            "message": "Documento em processamento na esteira de extracao IDP e OCR.",
            "extraction": None,
            "error": None,
            "created_at": "2026-10-12T19:00:00Z",
            "updated_at": "2026-10-12T19:00:02Z",
        },
    },
    "falha": {
        "summary": "Falha no processamento",
        "description": "Detalhes estruturados do erro ocorrido durante a extracao.",
        "value": {
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "arquivo_danificado.pdf",
            "status": "EXTRACTION_FAILED",
            "progress": 0.0,
            "message": "Falha durante o processamento documental.",
            "extraction": None,
            "error": {
                "code": "EXTRACTION_FAILED",
                "message": "Erro ao extrair conteudo do documento: Arquivo corrompido.",
                "details": {
                    "stage": "pdfplumber_parsing",
                    "error_class": "RuntimeError",
                },
                "timestamp": "2026-10-12T19:00:03Z",
            },
            "created_at": "2026-10-12T19:00:00Z",
            "updated_at": "2026-10-12T19:00:03Z",
        },
    },
}


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de Documento PDF para Ingestao",
)
def upload_document(
    file: UploadFile = File(...),
    async_process: bool = Query(
        False, description="Executar extracao de forma assincrona via Celery"
    ),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    """
    Recebe um arquivo PDF, valida assinatura binaria (%PDF-), persiste no MinIO
    e inicia o processamento IDP sincrono ou assincrono via Celery.
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
        logger.warning(
            f"Falha no upload para o MinIO: {str(storage_err)}. "
            f"Mantendo copia local em {destination_path}"
        )

    # Criacao do registro no banco
    initial_status = (
        ProcessingStatus.PROCESSING.value if async_process else ProcessingStatus.PENDING.value
    )
    doc = Document(
        id=doc_id,
        filename=safe_filename,
        original_filename=file.filename,
        content_type=file.content_type or "application/pdf",
        file_size=file_size,
        storage_path=storage_path,
        status=initial_status,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    if async_process:
        try:
            process_document_task.delay(doc.id, destination_path, safe_filename)
        except Exception as task_err:
            logger.warning(f"Celery nao disponivel: {str(task_err)}. Executando sincronamente.")
            async_process = False

    if not async_process:
        try:
            extractor = DocumentExtractor()
            extracted = extractor.extract(destination_path, document_id=doc.id)
            doc.extracted_text = extracted.get("full_text")
            doc_metadata = extracted.get("metadata") or {}

            # Processamento de entidades tipadas e evidencias ancoradas
            extraction_res = extract_fields_and_evidence(
                text=doc.extracted_text or "",
                pages=extracted.get("pages"),
            )
            doc_metadata["pages"] = extracted.get("pages", [])
            doc_metadata["extraction"] = extraction_res.model_dump()
            doc.extracted_metadata = doc_metadata
            doc.status = ProcessingStatus.COMPLETED.value
        except Exception as ex:
            doc.status = ProcessingStatus.EXTRACTION_FAILED.value
            doc.extracted_metadata = {
                "error": str(ex),
                "error_detail": {
                    "code": ProcessingStatus.EXTRACTION_FAILED.value,
                    "message": str(ex),
                    "details": {"stage": "idp_extraction"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        db.commit()
        db.refresh(doc)

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.original_filename,
        original_filename=doc.original_filename,
        status=ProcessingStatus(doc.status),
        file_size=doc.file_size,
        total_pages=(
            (doc.extracted_metadata.get("total_pages") or 0) if doc.extracted_metadata else 0
        ),
        created_at=doc.created_at,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Listar Documentos Ingeridos",
)
def list_documents(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
) -> DocumentListResponse:
    """Retorna lista paginada de documentos processados."""
    docs = db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Document).count()
    return DocumentListResponse(
        total=total,
        items=[
            DocumentListItem(
                id=d.id,
                original_filename=d.original_filename,
                status=ProcessingStatus(d.status),
                file_size=d.file_size,
                created_at=d.created_at,
                total_pages=(
                    (d.extracted_metadata.get("total_pages") or 0) if d.extracted_metadata else 0
                ),
            )
            for d in docs
        ],
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Obter Detalhes do Documento e Texto Extraido",
)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    """Retorna dados detalhados do documento pelo identificador unico."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        )

    return DocumentDetailResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        status=ProcessingStatus(doc.status),
        file_size=doc.file_size,
        storage_path=doc.storage_path,
        created_at=doc.created_at,
        metadata=doc.extracted_metadata,
        extracted_text_preview=((doc.extracted_text[:1000] + "...") if doc.extracted_text else ""),
    )


@router.get(
    "/{document_id}/processing",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar Estado Atual e Resultado da Extracao",
    description=(
        "Consulta o estado atual do processamento e o resultado detalhado da extracao IDP "
        "para um documento especifico atraves de seu identificador unico (UUID). "
        "Retorna o payload completo com evidencias para processamentos concluidos, "
        "indicador de progresso para documentos em processamento, "
        "ou estrutura de erro detalhada em casos de falha."
    ),
    responses={
        200: {
            "description": "Estado e resultado da extracao retornados com sucesso.",
            "content": {
                "application/json": {
                    "examples": PROCESSING_EXAMPLES,
                }
            },
        },
        404: {
            "description": "Documento nao encontrado.",
            "model": ErrorResponse,
        },
    },
)
@router.get(
    "/{document_id}/status",
    response_model=ProcessingStatusResponse,
    include_in_schema=False,
)
@router.get(
    "/{document_id}/extraction",
    response_model=ProcessingStatusResponse,
    include_in_schema=False,
)
def get_document_processing_status(
    document_id: str, db: Session = Depends(get_db)
) -> ProcessingStatusResponse:
    """
    Retorna o estado atual e o resultado da extracao por identificador unico.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        )
    return build_processing_status_response(doc)

"""Document ingestion and retrieval endpoints."""

import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.idp.extractor import DocumentExtractor

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/conformia_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload de Documento PDF para Ingestão")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Recebe um arquivo PDF, valida o formato, persiste no storage e inicia a extração IDP.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos no formato PDF são suportados pelo Conform.IA BNDES."
        )

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{os.path.basename(file.filename)}"
    destination_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(destination_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gravar arquivo em disco: {str(e)}"
        )

    # Criação do registro no banco
    doc = Document(
        id=doc_id,
        filename=safe_filename,
        original_filename=file.filename,
        content_type=file.content_type or "application/pdf",
        file_size=file_size,
        storage_path=destination_path,
        status="PROCESSING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Executa extração síncrona / imediata (ou pode disparar celery task)
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
        "filename": doc.original_filename,
        "status": doc.status,
        "file_size": doc.file_size,
        "total_pages": doc.extracted_metadata.get("total_pages") if doc.extracted_metadata else 0,
        "created_at": doc.created_at.isoformat()
    }


@router.get("", summary="Listar Documentos Ingeridos")
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
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
                "total_pages": d.extracted_metadata.get("total_pages") if d.extracted_metadata else 0
            }
            for d in docs
        ]
    }


@router.get("/{document_id}", summary="Obter Detalhes do Documento e Texto Extraído")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retorna dados detalhados do documento pelo identificador único."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "status": doc.status,
        "file_size": doc.file_size,
        "storage_path": doc.storage_path,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "metadata": doc.extracted_metadata,
        "extracted_text_preview": (doc.extracted_text[:1000] + "...") if doc.extracted_text else ""
    }

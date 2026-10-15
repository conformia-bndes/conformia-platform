"""Pydantic schemas for Document entities and ingestion responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import ProcessingStatus


class DocumentBase(BaseModel):
    """Schema base para atributos comuns de documentos."""

    model_config = ConfigDict(from_attributes=True)

    filename: str = Field(..., description="Nome do arquivo armazenado no sistema")
    original_filename: str = Field(..., description="Nome original do arquivo submetido")
    content_type: str = Field(default="application/pdf", description="MIME type do documento")
    file_size: int = Field(..., ge=0, description="Tamanho do arquivo em bytes")


class DocumentUploadResponse(BaseModel):
    """Resposta do endpoint de upload de documentos."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Identificador unico (UUID) do documento")
    task_id: Optional[str] = Field(
        default=None, description="Identificador da tarefa assincrona no Celery"
    )
    filename: str = Field(..., description="Nome do arquivo processado")
    original_filename: Optional[str] = Field(default=None, description="Nome original do arquivo")
    status: ProcessingStatus = Field(..., description="Estado atual do processamento")
    file_size: int = Field(..., ge=0, description="Tamanho em bytes")
    total_pages: Optional[int] = Field(default=0, description="Total de paginas detectadas")
    created_at: datetime = Field(..., description="Timestamp de criacao do registro")


class DocumentListItem(BaseModel):
    """Item resumido para listagem paginada de documentos."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Identificador unico (UUID) do documento")
    original_filename: str = Field(..., description="Nome original do arquivo")
    status: ProcessingStatus = Field(..., description="Estado do documento")
    file_size: int = Field(..., ge=0, description="Tamanho em bytes")
    created_at: Optional[datetime] = Field(default=None, description="Data/hora de envio")
    total_pages: Optional[int] = Field(default=0, description="Total de paginas")


class DocumentListResponse(BaseModel):
    """Resposta paginada da listagem de documentos."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., ge=0, description="Total de documentos cadastrados")
    items: List[DocumentListItem] = Field(
        default_factory=list, description="Lista paginada de documentos"
    )


class DocumentDetailResponse(BaseModel):
    """Detalhes completos de um documento cadastrado."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Identificador unico (UUID)")
    original_filename: str = Field(..., description="Nome original do arquivo")
    status: ProcessingStatus = Field(..., description="Estado atual do processamento")
    file_size: int = Field(..., ge=0, description="Tamanho em bytes")
    storage_path: str = Field(..., description="Caminho ou URI de armazenamento")
    created_at: Optional[datetime] = Field(default=None, description="Data/hora de criacao")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadados de extracao e documento"
    )
    extracted_text_preview: Optional[str] = Field(
        default=None, description="Previa do texto extraido"
    )

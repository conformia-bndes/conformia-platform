"""Pydantic schemas for processing status and extraction query endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import ProcessingStatus
from app.schemas.error import ErrorDetail
from app.schemas.extraction import ExtractionResult


class ProcessingStatusResponse(BaseModel):
    """
    Resposta do endpoint de consulta de estado e resultado de extracao.

    Acomoda os estados:
    - Sucesso: status COMPLETED com payload de extracao e evidencias populados.
    - Em processamento: status PENDING ou PROCESSING com indicador de progresso.
    - Falha: status FAILED ou EXTRACTION_FAILED com detalhes estruturados do erro.
    """

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(
        ...,
        description="Identificador unico (UUID) do documento",
    )
    filename: str = Field(
        ...,
        description="Nome original do arquivo submetido",
    )
    status: ProcessingStatus = Field(
        ...,
        description="Estado atual do processamento do documento",
    )
    progress: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Progresso estimado do processamento (0.0 a 1.0)",
    )
    message: str = Field(
        ...,
        description="Mensagem descritiva do estado atual",
    )
    extraction: Optional[ExtractionResult] = Field(
        default=None,
        description="Resultado estruturado da extracao (presente quando COMPLETED)",
    )
    error: Optional[ErrorDetail] = Field(
        default=None,
        description="Detalhes estruturados do erro (presente quando FAILED ou EXTRACTION_FAILED)",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp de criacao do documento",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp da ultima atualizacao do processamento",
    )

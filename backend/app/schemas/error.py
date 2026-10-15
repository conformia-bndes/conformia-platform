"""Pydantic schemas for structured errors and error responses."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


def get_current_utc_time() -> datetime:
    """Retorna timestamp atual em UTC."""
    return datetime.now(timezone.utc)


class ErrorDetail(BaseModel):
    """Estrutura detalhada de erro operacional ou de processamento."""

    model_config = ConfigDict(from_attributes=True)

    code: str = Field(
        ...,
        description="Codigo padronizado do erro (ex.: EXTRACTION_FAILED, NOT_FOUND)",
        min_length=1,
    )
    message: str = Field(
        ...,
        description="Descricao compreensivel do erro ocorrido",
        min_length=1,
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalhes tecnicos adicionais ou contexto da falha",
    )
    timestamp: datetime = Field(
        default_factory=get_current_utc_time,
        description="Timestamp UTC de ocorrencia do erro",
    )


class ErrorResponse(BaseModel):
    """Resposta padrao de erro da API."""

    model_config = ConfigDict(from_attributes=True)

    error: ErrorDetail = Field(
        ...,
        description="Estrutura de erro padronizada",
    )

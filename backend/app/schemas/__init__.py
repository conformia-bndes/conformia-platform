"""Pydantic v2 schemas package for Conform.IA BNDES."""

from app.schemas.document import (
    DocumentBase,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.schemas.enums import ProcessingStatus
from app.schemas.error import ErrorDetail, ErrorResponse
from app.schemas.evidence import PageEvidence
from app.schemas.extraction import ExtractedField, ExtractionResult
from app.schemas.processing import ProcessingStatusResponse

__all__ = [
    "ProcessingStatus",
    "PageEvidence",
    "ExtractedField",
    "ExtractionResult",
    "ErrorDetail",
    "ErrorResponse",
    "DocumentBase",
    "DocumentUploadResponse",
    "DocumentListItem",
    "DocumentListResponse",
    "DocumentDetailResponse",
    "ProcessingStatusResponse",
]

"""Enumerations for processing statuses and document workflows."""

from enum import Enum


class ProcessingStatus(str, Enum):
    """Estados do ciclo de vida de processamento de um documento."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"

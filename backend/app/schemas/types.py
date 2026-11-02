"""Tipos Pydantic compartilhados pelos schemas da API."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def _assume_utc(value: datetime) -> datetime:
    """Marca como UTC os timestamps sem fuso (o banco guarda datetime.utcnow(), em UTC)."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


# Timestamp sempre com fuso na resposta (RFC 3339), como o OpenAPI declara em `date-time`.
UTCDateTime = Annotated[datetime, AfterValidator(_assume_utc)]

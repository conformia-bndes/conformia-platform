"""Pydantic schemas for extracted fields and IDP payload results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.evidence import PageEvidence


class ExtractedField(BaseModel):
    """Representacao tipada de um campo individual extraido de um documento."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        ...,
        description="Nome identificador do campo extraido (ex.: cnpj, data_validade)",
        min_length=1,
    )
    value: Any = Field(
        ...,
        description="Valor normalizado do campo extraido",
    )
    raw_value: Optional[str] = Field(
        default=None,
        description="Valor textual literal encontrado no documento",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Grau de confianca da extracao do campo",
    )
    evidence: Optional[PageEvidence] = Field(
        default=None,
        description="Evidencia textual e de pagina associada ao campo",
    )


class ExtractionResult(BaseModel):
    """
    Resultado estruturado completo da extracao documental IDP.

    Agrega tipologia do documento, campos extraidos normalizados,
    evidencias textuais referenciadas por pagina e dados tabulares.
    """

    model_config = ConfigDict(from_attributes=True)

    document_type: Optional[str] = Field(
        default=None,
        description="Tipologia do documento identificada (ex.: CND_FEDERAL, CRF_FGTS)",
    )
    fields: Dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Dicionario de campos tipados extraidos",
    )
    evidences: List[PageEvidence] = Field(
        default_factory=list,
        description="Lista de evidencias textuais ancoradas por pagina",
    )
    total_pages: int = Field(
        default=0,
        ge=0,
        description="Total de paginas analisadas",
    )
    tables: List[Any] = Field(
        default_factory=list,
        description="Tabelas extraidas das paginas do documento",
    )
    full_text_preview: Optional[str] = Field(
        default=None,
        description="Previa do texto extraido (primeiros caracteres)",
    )

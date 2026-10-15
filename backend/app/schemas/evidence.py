"""Pydantic schemas for textual and page-anchored evidence."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PageEvidence(BaseModel):
    """
    Evidencia textual com ancoragem na pagina do documento.

    Atende aos principios de explicabilidade do Conform.IA BNDES,
    permitindo que tanto o Maker quanto o Checker e o analista humano
    identifiquem exatamente a citacao literal e a pagina correspondente.
    """

    model_config = ConfigDict(from_attributes=True)

    text: str = Field(
        ...,
        description="Citacao textual exata ou trecho de evidencia extraido do documento",
        min_length=1,
    )
    page: int = Field(
        ...,
        description="Numero da pagina onde a evidencia foi localizada (1-indexed)",
        ge=1,
    )
    confidence: float = Field(
        default=1.0,
        description="Grau de confianca da extracao da evidencia (entre 0.0 e 1.0)",
        ge=0.0,
        le=1.0,
    )
    bounding_box: Optional[List[float]] = Field(
        default=None,
        description="Coordenadas da bounding box da evidencia na pagina [x0, y0, x1, y1]",
    )

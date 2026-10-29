"""Pydantic schemas for human Maker-Checker review of compliance reports."""

from datetime import datetime
from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ReviewDecision = Literal["APPROVE", "REJECT", "EXCEPTION"]
ReviewState = Literal["NO_REVIEW", "PENDING_CHECK", "FINAL", "RETURNED"]

Justification = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=20, max_length=4000)
]
Comment = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=4000)]


class ReviewProposalRequest(BaseModel):
    """Proposta do analista (Maker) sobre o laudo automatizado."""

    decision: ReviewDecision = Field(
        ...,
        description=(
            "APPROVE ou REJECT o laudo; EXCEPTION defere excecao motivada. "
            "Laudo NON_COMPLIANT so pode ser aceito via EXCEPTION."
        ),
    )
    justification: Justification = Field(..., description="Parecer tecnico (20 a 4000 caracteres)")


class ReviewResolutionRequest(BaseModel):
    """Parecer do segundo analista (Checker) ao confirmar ou devolver a proposta."""

    comment: Comment = Field(..., description="Parecer do revisor (10 a 4000 caracteres)")


class ReviewEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    event_type: Literal["PROPOSED", "CONFIRMED", "RETURNED"]
    decision: Optional[ReviewDecision] = None
    justification: str
    resolves_id: Optional[str] = None
    report_status: Optional[str] = None
    actor_id: str
    actor_role: str
    created_at: datetime


class ReviewStateResponse(BaseModel):
    document_id: str
    state: ReviewState = Field(
        ...,
        description=(
            "NO_REVIEW: sem proposta; PENDING_CHECK: proposta aguardando segundo analista; "
            "FINAL: ultima resolucao confirmou a proposta; RETURNED: ultima proposta devolvida."
        ),
    )
    final_decision: Optional[ReviewDecision] = Field(
        default=None, description="Decisao da proposta confirmada mais recente"
    )
    pending_proposal_id: Optional[str] = None
    events: List[ReviewEventResponse] = Field(default_factory=list)

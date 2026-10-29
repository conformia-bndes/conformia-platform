"""Human Maker-Checker review endpoints (RF09) over the automated compliance report."""

import logging
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import Principal, require_role
from app.db.session import get_db
from app.schemas.review import (
    ReviewEventResponse,
    ReviewProposalRequest,
    ReviewResolutionRequest,
    ReviewStateResponse,
)
from app.services.review_service import (
    ReviewError,
    get_review_state,
    propose_decision,
    resolve_proposal,
)

router = APIRouter()
logger = logging.getLogger(__name__)

require_analyst = require_role("ANALISTA")


def _run_write(db: Session, action: Callable[[], object]):
    """Executa a acao e faz commit, traduzindo violacoes de regra para HTTP."""
    try:
        result = action()
        db.commit()
        return result
    except ReviewError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except IntegrityError as exc:
        # Duas resolucoes concorrentes da mesma proposta: a restricao unica decide.
        db.rollback()
        logger.info("Resolucao concorrente rejeitada pela restricao unica de review_events.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Proposta ja resolvida."
        ) from exc


@router.get(
    "/{document_id}",
    response_model=ReviewStateResponse,
    summary="Consultar Estado e Historico da Revisao Humana",
)
def get_review(document_id: str, db: Session = Depends(get_db)) -> ReviewStateResponse:
    try:
        return ReviewStateResponse.model_validate(get_review_state(db, document_id))
    except ReviewError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/{document_id}",
    response_model=ReviewEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Propor Decisao Humana sobre o Laudo (Maker)",
)
def propose(
    document_id: str,
    body: ReviewProposalRequest,
    principal: Principal = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> ReviewEventResponse:
    event = _run_write(
        db,
        lambda: propose_decision(db, document_id, body.decision, body.justification, principal),
    )
    return ReviewEventResponse.model_validate(event)


@router.post(
    "/{document_id}/{proposal_id}/confirm",
    response_model=ReviewEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar Proposta de Outro Analista (Checker)",
)
def confirm(
    document_id: str,
    proposal_id: str,
    body: ReviewResolutionRequest,
    principal: Principal = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> ReviewEventResponse:
    event = _run_write(
        db,
        lambda: resolve_proposal(
            db, document_id, proposal_id, "CONFIRMED", body.comment, principal
        ),
    )
    return ReviewEventResponse.model_validate(event)


@router.post(
    "/{document_id}/{proposal_id}/return",
    response_model=ReviewEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Devolver Proposta de Outro Analista (Checker)",
)
def return_proposal(
    document_id: str,
    proposal_id: str,
    body: ReviewResolutionRequest,
    principal: Principal = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> ReviewEventResponse:
    event = _run_write(
        db,
        lambda: resolve_proposal(db, document_id, proposal_id, "RETURNED", body.comment, principal),
    )
    return ReviewEventResponse.model_validate(event)

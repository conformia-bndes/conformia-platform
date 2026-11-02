from fastapi import APIRouter, Depends
from app.api.v1.endpoints import health, documents, compliance, reviews
from app.core.security import verify_api_key
from app.schemas.error import HTTPErrorResponse

api_router = APIRouter()

# Respostas de erro comuns, declaradas no OpenAPI para todas as rotas protegidas.
PROTECTED_RESPONSES = {
    401: {"model": HTTPErrorResponse, "description": "Chave de API ausente ou invalida."},
    403: {"model": HTTPErrorResponse, "description": "Perfil sem permissao para a operacao."},
    404: {"model": HTTPErrorResponse, "description": "Recurso nao encontrado."},
}

api_router.include_router(health.router, prefix="/health", tags=["Saude & Diagnosticos"])

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documentos & Ingestao IDP"],
    dependencies=[Depends(verify_api_key)],
    responses=PROTECTED_RESPONSES,
)

api_router.include_router(
    reviews.router,
    prefix="/compliance/reviews",
    tags=["Revisao Humana (Maker-Checker)"],
    dependencies=[Depends(verify_api_key)],
    responses=PROTECTED_RESPONSES,
)

api_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["Conformidade & Auditoria"],
    dependencies=[Depends(verify_api_key)],
    responses=PROTECTED_RESPONSES,
)

"""Aggregated API v1 router definition."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, compliance

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Saúde & Diagnósticos"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documentos & Ingestão IDP"]
)

api_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["Conformidade & Auditoria"]
)

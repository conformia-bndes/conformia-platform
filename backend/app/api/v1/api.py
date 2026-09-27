from fastapi import APIRouter, Depends
from app.api.v1.endpoints import health, documents, compliance
from app.core.security import verify_api_key

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Saude & Diagnosticos"])

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documentos & Ingestao IDP"],
    dependencies=[Depends(verify_api_key)],
)

api_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["Conformidade & Auditoria"],
    dependencies=[Depends(verify_api_key)],
)

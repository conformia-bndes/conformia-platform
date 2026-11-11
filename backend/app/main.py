"""Conform.IA BNDES Platform - FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import InterfaceError, OperationalError
from app.api.v1.api import api_router
from app.core.config import settings

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conformia.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida da aplicação. O esquema do banco vem somente das migrations Alembic
    (`python -m app.db.migrate`, executado antes da API e do worker), nunca de create_all.
    """
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")

    yield

    logger.info(f"Finalizando conexões e encerrando {settings.PROJECT_NAME}.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Plataforma SaaS de Processamento Inteligente de Documentos (IDP) "
        "para verificação automatizada de conformidade no BNDES - Consulta Pública nº 01/2025."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuração do Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Banco de dados indisponivel (conexao recusada, timeout, conexao perdida): e uma falha
# temporaria de dependencia, nao um defeito da API. Responde 503 para o cliente tentar de novo.
@app.exception_handler(OperationalError)
@app.exception_handler(InterfaceError)
async def database_unavailable_handler(request: Request, exc: Exception):
    logger.error("Banco de dados indisponivel em %s: %s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Servico temporariamente indisponivel. Tente novamente em instantes."},
        headers={"Retry-After": "5"},
    )


# Tratamento Global de Exceções
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Exceção não tratada na rota {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "Ocorreu um erro interno no servidor ao processar a requisição.",
            "detail": str(exc) if settings.DEBUG else None,
            "path": request.url.path,
        },
    )


# Roteamento Modular da API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Bem-vindo ao {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "version": settings.VERSION,
    }

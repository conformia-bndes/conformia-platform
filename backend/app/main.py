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


_DOCS_PATHS = {
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    f"{settings.API_V1_STR}/openapi.json",
}


def create_app() -> FastAPI:
    """
    Fabrica da aplicacao FastAPI.

    Decisao arquitetural (Issue #172 / AUD-18b / RNF01):
    Em `ENVIRONMENT=production`, a documentacao interativa (`/docs`, `/redoc`) e o esquema
    OpenAPI (`/api/v1/openapi.json`) sao desativados (retornam HTTP 404) para nao expor a
    superficie interna da API em producao. Fora de producao (`development` e `test`), permanecem
    ativos para depuracao local e para o fuzzing de contrato (Schemathesis) no CI.
    """
    is_production = settings.ENVIRONMENT == "production"
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Plataforma SaaS de Processamento Inteligente de Documentos (IDP) "
            "para verificação automatizada de conformidade no BNDES - Consulta Pública nº 01/2025."
        ),
        openapi_url=None if is_production else f"{settings.API_V1_STR}/openapi.json",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def disable_openapi_docs_in_production(request: Request, call_next):
        if settings.ENVIRONMENT == "production" and request.url.path in _DOCS_PATHS:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Not Found"},
            )
        return await call_next(request)

    # Configuração do Middleware de CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Banco de dados indisponivel (conexao recusada, timeout, conexao perdida): e uma falha
    # temporaria de dependencia, nao um defeito da API. Responde 503 para o cliente tentar de novo.
    @application.exception_handler(OperationalError)
    @application.exception_handler(InterfaceError)
    async def database_unavailable_handler(request: Request, exc: Exception):
        logger.error("Banco de dados indisponivel em %s: %s", request.url.path, type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Servico temporariamente indisponivel. Tente novamente em instantes."
            },
            headers={"Retry-After": "5"},
        )

    # Tratamento Global de Exceções
    @application.exception_handler(Exception)
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
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/", tags=["Root"])
    def root():
        return {
            "message": f"Bem-vindo ao {settings.PROJECT_NAME}",
            "docs": None if settings.ENVIRONMENT == "production" else "/docs",
            "health": f"{settings.API_V1_STR}/health",
            "version": settings.VERSION,
        }

    return application


app = create_app()

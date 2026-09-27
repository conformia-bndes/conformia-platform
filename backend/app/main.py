"""Conform.IA BNDES Platform - FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine, Base

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conformia.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciamento do ciclo de vida da aplicação:
    Cria tabelas relacionais em banco local (dev/demo) e inicializa pools.
    """
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    try:
        # Garante a criação de tabelas para bootstrap imediato em dev/testes
        Base.metadata.create_all(bind=engine)
        logger.info("Esquemas de banco de dados verificados/criados com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar tabelas no banco de dados: {e}")

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

"""Health check and system diagnostics endpoint."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", summary="Verificação de Saúde da API e Dependências")
def get_health(db: Session = Depends(get_db)):
    """
    Retorna o status operacional da plataforma, versão, ambiente e conectividade
    com PostgreSQL e Redis.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "degraded"

    redis_status = "healthy"
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_status = "degraded"

    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
            "minio": "ready"
        }
    }

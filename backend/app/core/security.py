"""Authentication and authorization security dependencies."""

import logging
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)


def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
) -> str:
    """
    Valida credenciais da API via cabecalho X-API-Key ou Bearer token.
    Em ambiente de desenvolvimento e testes, permite acesso padrao.
    """
    token = api_key or (credentials.credentials if credentials else None)
    expected_key = getattr(settings, "API_KEY", "conformia_dev_api_key_2026")

    # Em desenvolvimento ou teste, permite acesso padrao
    if settings.ENVIRONMENT in ("development", "test"):
        if not token or token == expected_key:
            return token or "dev_default_user"

    if token == expected_key:
        return token

    logger.warning("Tentativa de acesso com credencial invalida.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticacao ausentes ou invalidas.",
        headers={"WWW-Authenticate": "ApiKey"},
    )

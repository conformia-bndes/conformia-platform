"""Authentication and authorization security dependencies."""

import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Callable, Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """Usuario autenticado. Nunca carrega a chave usada na autenticacao."""

    user_id: str
    role: str


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def resolve_principal(token: Optional[str]) -> Optional[Principal]:
    """Identifica o usuario dono da chave pessoal; None se a chave nao pertence a ninguem."""
    if not token:
        return None
    digest = hash_api_key(token)
    for user in settings.API_USERS:
        if hmac.compare_digest(digest, user.key_sha256):
            return Principal(user_id=user.user_id, role=user.role)
    return None


def _extract_token(
    api_key: Optional[str], credentials: Optional[HTTPAuthorizationCredentials]
) -> Optional[str]:
    return api_key or (credentials.credentials if credentials else None)


def _is_service_key(token: Optional[str]) -> bool:
    return bool(token) and hmac.compare_digest(token, settings.API_KEY)


def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
) -> str:
    """
    Valida credenciais da API via cabecalho X-API-Key ou Bearer token: a chave de servico
    (API_KEY) ou uma chave pessoal de API_USERS.
    Em ambiente de desenvolvimento e testes, permite acesso padrao sem credencial.
    """
    token = _extract_token(api_key, credentials)

    # Em desenvolvimento ou teste, permite acesso padrao
    if settings.ENVIRONMENT in ("development", "test") and not token:
        return "dev_default_user"

    if _is_service_key(token):
        return "service"

    principal = resolve_principal(token)
    if principal is not None:
        return principal.user_id

    logger.warning("Tentativa de acesso com credencial invalida.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticacao ausentes ou invalidas.",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def require_role(*roles: str) -> Callable[..., Principal]:
    """
    Dependencia que exige um usuario identificado por chave pessoal com um dos papeis.
    Nao ha acesso anonimo nem pela chave de servico, em nenhum ambiente: decisoes humanas
    precisam de autor identificavel.
    """

    def dependency(
        api_key: Optional[str] = Security(api_key_header),
        credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
    ) -> Principal:
        principal = resolve_principal(_extract_token(api_key, credentials))
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Operacao exige chave de API pessoal de um usuario cadastrado.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        if principal.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Perfil {principal.role} nao autorizado para esta operacao.",
            )
        return principal

    return dependency

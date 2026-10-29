"""Authentication and authorization security dependencies."""

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from functools import lru_cache
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


API_KEY_HASH_ITERATIONS = 200_000


def hash_api_key(
    secret: str, salt: Optional[bytes] = None, iterations: int = API_KEY_HASH_ITERATIONS
) -> str:
    """Hash PBKDF2-HMAC-SHA256 com sal aleatorio, no formato aceito por API_USERS.key_hash."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


@lru_cache(maxsize=256)
def _secret_matches(secret: str, encoded_hash: str) -> bool:
    """
    Compara o segredo com o hash configurado. O resultado fica em cache por processo para
    que cada chave pague o custo do PBKDF2 uma vez; o cache vive so na memoria do processo.
    """
    _, iterations, salt_hex, digest_hex = encoded_hash.split("$")
    candidate = hashlib.pbkdf2_hmac(
        "sha256", secret.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
    )
    return hmac.compare_digest(candidate.hex(), digest_hex)


# Hash de referencia para usuarios inexistentes: o tempo de resposta nao revela quais
# user_id estao cadastrados.
_UNKNOWN_USER_HASH = hash_api_key(secrets.token_urlsafe(32))


def resolve_principal(token: Optional[str]) -> Optional[Principal]:
    """
    Identifica o dono de uma chave pessoal no formato "<user_id>:<segredo>". O prefixo
    limita a verificacao a um unico hash PBKDF2 por requisicao, mesmo com chave invalida.
    """
    if not token or ":" not in token:
        return None
    user_id, secret = token.split(":", 1)
    user = next((u for u in settings.API_USERS if u.user_id == user_id), None)
    if user is None:
        _secret_matches(secret, _UNKNOWN_USER_HASH)
        return None
    if not _secret_matches(secret, user.key_hash):
        return None
    return Principal(user_id=user.user_id, role=user.role)


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

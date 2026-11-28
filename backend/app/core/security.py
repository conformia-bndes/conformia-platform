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
    auth_type: str = "personal"  # "personal", "service", "anonymous"


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


def authenticate_principal(
    api_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
) -> Principal:
    """
    Resolve a identidade autenticada via X-API-Key ou Bearer token.
    - Chave pessoal (`API_USERS`): Principal(user_id, role, auth_type="personal").
    - Chave de servico (`API_KEY`): Principal("service", "SERVICE", auth_type="service").
    - Acesso anonimo: somente com ALLOW_ANONYMOUS_ACCESS=true (nunca em producao).
    """
    token = _extract_token(api_key, credentials)

    if settings.ALLOW_ANONYMOUS_ACCESS and not token:
        return Principal(user_id="dev_default_user", role="ADMIN", auth_type="anonymous")

    if _is_service_key(token):
        return Principal(user_id="service", role="SERVICE", auth_type="service")

    principal = resolve_principal(token)
    if principal is not None:
        return principal

    logger.warning("Tentativa de acesso com credencial invalida.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticacao ausentes ou invalidas.",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
) -> str:
    """
    Valida credenciais da API via cabecalho X-API-Key ou Bearer token e retorna o
    identificador do executor (`user_id`, `"service"` ou `"dev_default_user"`).
    """
    return authenticate_principal(api_key=api_key, credentials=credentials).user_id


def require_access(*roles: str, allow_service: bool = False) -> Callable[..., Principal]:
    """
    Dependencia de RBAC por rota: exige autenticacao e perfil autorizado.
    - `allow_service=True` permite a chave de servico (`API_KEY`) apenas nas rotas de
      automacao explicitamente documentadas (smoke, carga, resiliencia, leitura/ingestao).
    - Em modo `ALLOW_ANONYMOUS_ACCESS=true` (apenas dev/test), retorna `dev_default_user`.
    """

    def dependency(
        api_key: Optional[str] = Security(api_key_header),
        credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
    ) -> Principal:
        principal = authenticate_principal(api_key=api_key, credentials=credentials)
        if principal.auth_type == "anonymous":
            return principal
        if principal.auth_type == "service":
            if allow_service:
                return principal
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chave de servico nao autorizada para esta operacao.",
            )
        if principal.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Perfil {principal.role} nao autorizado para esta operacao.",
            )
        return principal

    return dependency


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


# Matriz RBAC padrao por tipo de rota (ADR-005 / Issue #163)
require_read_access = require_access("ANALISTA", "AUDITOR", "ADMIN", allow_service=True)
require_write_access = require_access("ANALISTA", "ADMIN", allow_service=True)
require_audit_access = require_access("ANALISTA", "AUDITOR", "ADMIN", allow_service=True)

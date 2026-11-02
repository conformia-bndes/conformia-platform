"""
Cobertura de autenticacao de todas as rotas da API em modo producao.

Em vez de listar endpoints a mao, o teste percorre as rotas registradas no app: um endpoint
novo sem autenticacao reprova aqui, sem que ninguem precise lembrar de incluir o caso.
"""

import pytest

from app.core.config import settings
from app.main import app

# Rotas publicas por desenho: sondagem de saude e raiz informativa.
PUBLIC_PATHS = {"/", f"{settings.API_V1_STR}/health"}
METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}


# Rotas de compatibilidade fora do OpenAPI (include_in_schema=False) que tambem exigem chave.
HIDDEN_ROUTES = [
    ("GET", f"{settings.API_V1_STR}/documents/{{document_id}}/status"),
    ("GET", f"{settings.API_V1_STR}/documents/{{document_id}}/extraction"),
]


def _protected_routes():
    """Inventario a partir do contrato publico (OpenAPI), que independe de detalhes internos."""
    seen = set()
    for path, operations in app.openapi()["paths"].items():
        if path in PUBLIC_PATHS:
            continue
        for method in operations:
            if method.upper() not in {"HEAD", "OPTIONS"}:
                seen.add((method.upper(), path))
    seen.update(HIDDEN_ROUTES)
    return seen


def _concrete(path: str) -> str:
    """Troca parametros de caminho ({document_id}) por um valor qualquer."""
    out, depth = [], 0
    for char in path:
        if char == "{":
            depth += 1
            out.append("x")
        elif char == "}":
            depth -= 1
        elif depth == 0:
            out.append(char)
    return "".join(out)


ROUTES = sorted(_protected_routes())


@pytest.fixture(autouse=True)
def production_mode(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")


def test_route_inventory_is_not_empty():
    # Protege o proprio teste: se a descoberta de rotas quebrar, nada seria verificado.
    assert len(ROUTES) >= 10


@pytest.mark.parametrize("method,path", ROUTES)
def test_route_requires_credentials_in_production(client, method, path):
    kwargs = {"json": {}} if method in METHODS_WITH_BODY else {}
    response = client.request(method, _concrete(path), **kwargs)
    assert (
        response.status_code == 401
    ), f"{method} {path} respondeu {response.status_code} sem chave"


@pytest.mark.parametrize("method,path", ROUTES)
def test_route_rejects_invalid_key_in_production(client, method, path):
    kwargs = {"json": {}} if method in METHODS_WITH_BODY else {}
    response = client.request(
        method, _concrete(path), headers={"X-API-Key": "chave-invalida"}, **kwargs
    )
    assert response.status_code == 401, f"{method} {path} aceitou chave invalida"


def test_health_stays_public(client):
    assert client.get(f"{settings.API_V1_STR}/health").status_code == 200

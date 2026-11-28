"""
Cobertura de autenticacao e RBAC de todas as rotas da API em modo producao (Issue #163).

Em vez de listar endpoints a mao, o teste percorre as rotas registradas no app: um endpoint
novo sem autenticacao ou sem regra de autorizacao reprova aqui automaticamente.
"""

import io
import pytest

from app.core.config import ApiUser, settings
from app.core.security import hash_api_key
from app.db.models.compliance import AuditLog
from app.db.models.document import Document
from app.main import app

# Rotas publicas por desenho: sondagem de saude e raiz informativa.
PUBLIC_PATHS = {"/", f"{settings.API_V1_STR}/health"}
METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}

# Rotas de decisao humana: exigem chave pessoal (nunca chave de servico nem anonimo).
HUMAN_REVIEW_WRITE_ROUTES = {
    ("POST", f"{settings.API_V1_STR}/compliance/reviews/{{document_id}}"),
    ("POST", f"{settings.API_V1_STR}/compliance/reviews/{{document_id}}/{{proposal_id}}/confirm"),
    ("POST", f"{settings.API_V1_STR}/compliance/reviews/{{document_id}}/{{proposal_id}}/return"),
}

# Rotas de compatibilidade fora do OpenAPI (include_in_schema=False) que tambem exigem chave.
HIDDEN_ROUTES = [
    ("GET", f"{settings.API_V1_STR}/documents/{{document_id}}/status"),
    ("GET", f"{settings.API_V1_STR}/documents/{{document_id}}/extraction"),
]

RBAC_KEYS = {
    "analista": "ana.rbac:segredo-analista-rbac",
    "auditor": "aud.rbac:segredo-auditor-rbac",
    "admin": "adm.rbac:segredo-admin-rbac",
}
RBAC_HASHES = {role_key: hash_api_key(raw.split(":", 1)[1]) for role_key, raw in RBAC_KEYS.items()}


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
WRITE_ROUTES = [r for r in ROUTES if r[0] in METHODS_WITH_BODY]
READ_ROUTES = [r for r in ROUTES if r[0] == "GET"]


@pytest.fixture(autouse=True)
def production_mode(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_ACCESS", False)
    monkeypatch.setattr(
        settings,
        "API_USERS",
        [
            ApiUser(user_id="ana.rbac", role="ANALISTA", key_hash=RBAC_HASHES["analista"]),
            ApiUser(user_id="aud.rbac", role="AUDITOR", key_hash=RBAC_HASHES["auditor"]),
            ApiUser(user_id="adm.rbac", role="ADMIN", key_hash=RBAC_HASHES["admin"]),
        ],
    )


def _request_route(client, method: str, path: str, headers: dict | None = None):
    kwargs = {"headers": headers or {}}
    if method in METHODS_WITH_BODY:
        if path.endswith("/upload"):
            kwargs["files"] = {"file": ("x.txt", io.BytesIO(b"x"), "text/plain")}
        else:
            kwargs["json"] = {}
    return client.request(method, _concrete(path), **kwargs)


def test_route_inventory_is_not_empty():
    # Protege o proprio teste: se a descoberta de rotas quebrar, nada seria verificado.
    assert len(ROUTES) >= 10
    assert len(WRITE_ROUTES) >= 5
    assert len(READ_ROUTES) >= 5


@pytest.mark.parametrize("method,path", ROUTES)
def test_route_requires_credentials_in_production(client, method, path):
    response = _request_route(client, method, path)
    assert (
        response.status_code == 401
    ), f"{method} {path} respondeu {response.status_code} sem chave"


@pytest.mark.parametrize("method,path", ROUTES)
def test_route_rejects_invalid_key_in_production(client, method, path):
    response = _request_route(client, method, path, headers={"X-API-Key": "chave-invalida"})
    assert response.status_code == 401, f"{method} {path} aceitou chave invalida"


@pytest.mark.parametrize("method,path", WRITE_ROUTES)
def test_auditor_is_forbidden_on_all_write_routes(client, method, path):
    """RBAC (#163): perfil AUDITOR nunca pode gravar/alterar estado (HTTP 403)."""
    response = _request_route(client, method, path, headers={"X-API-Key": RBAC_KEYS["auditor"]})
    assert (
        response.status_code == 403
    ), f"AUDITOR deveria receber 403 em {method} {path}, obteve {response.status_code}"


@pytest.mark.parametrize("method,path", READ_ROUTES)
def test_auditor_can_access_all_read_routes(client, method, path):
    """RBAC (#163): perfil AUDITOR acessa consultas de documentos, laudos, revisoes e trilha."""
    response = _request_route(client, method, path, headers={"X-API-Key": RBAC_KEYS["auditor"]})
    assert response.status_code not in {
        401,
        403,
    }, f"AUDITOR foi barrado em {method} {path} com {response.status_code}"


@pytest.mark.parametrize("role_key", ["analista", "admin"])
@pytest.mark.parametrize("method,path", ROUTES)
def test_analista_and_admin_pass_rbac_on_all_routes(client, role_key, method, path):
    """RBAC (#163): ANALISTA e ADMIN passam na autorizacao de leitura, escrita e revisao."""
    response = _request_route(client, method, path, headers={"X-API-Key": RBAC_KEYS[role_key]})
    assert response.status_code not in {
        401,
        403,
    }, f"{role_key.upper()} barrado em {method} {path} com {response.status_code}"


@pytest.mark.parametrize("method,path", ROUTES)
def test_service_key_policy_across_all_routes(client, method, path):
    """
    Politica da chave de servico (ADR-005 / #163):
    - Recusada (401) em todas as rotas de decisao humana.
    - Permitida apenas nas rotas de leitura e ingestao/verificacao usadas por automacao/smoke.
    """
    response = _request_route(client, method, path, headers={"X-API-Key": settings.API_KEY})
    if (method, path) in HUMAN_REVIEW_WRITE_ROUTES:
        assert response.status_code == 401, f"API_KEY nao pode acessar decisao humana {path}"
    else:
        assert response.status_code not in {
            401,
            403,
        }, f"API_KEY deveria ser aceita na rota operacional {method} {path}"


def test_audit_records_real_executor_for_upload_verify_and_worker(
    client, db_session, monkeypatch, tmp_path
):
    """RF10 (#163): DOCUMENT_UPLOADED e COMPLIANCE_EVALUATION gravam user_id autenticado."""
    from app.api.v1.endpoints import documents
    from app.core.celery_app import process_document_task
    from tests.conftest import TestingSessionLocal
    from tests.synthetic_pdfs import build_native_pdf

    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSessionLocal)

    cnd_lines = [
        "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E A DIVIDA ATIVA DA UNIAO",
        "CNPJ: 12.345.678/0001-90",
        "Valida ate: 31/12/2099",
    ]
    pdf_bytes = build_native_pdf([cnd_lines])

    # 1. Upload sincrono autenticado como ana.rbac
    up = client.post(
        f"{settings.API_V1_STR}/documents/upload?async_process=false",
        files={"file": ("cnd_real.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"X-API-Key": RBAC_KEYS["analista"]},
    )
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]

    # 2. Verificacao explicita autenticada como adm.rbac
    ver = client.post(
        f"{settings.API_V1_STR}/compliance/verify/{doc_id}",
        headers={"X-API-Key": RBAC_KEYS["admin"]},
    )
    assert ver.status_code == 200, ver.text

    # 3. Propagacao do autor do upload quando o worker Celery avalia o documento
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    doc_path = tmp_path / f"{doc_id}_worker_cnd.pdf"
    doc_path.write_bytes(pdf_bytes)
    worker_res = process_document_task(doc_id, str(doc_path))
    assert worker_res["status"] == "COMPLETED"

    # 4. Consulta na trilha via perfil AUDITOR
    trail_resp = client.get(
        f"{settings.API_V1_STR}/compliance/audit-trail?limit=50",
        headers={"X-API-Key": RBAC_KEYS["auditor"]},
    )
    assert trail_resp.status_code == 200
    items = [item for item in trail_resp.json()["items"] if item["entity_id"] == doc_id]

    upload_events = [item for item in items if item["action"] == "DOCUMENT_UPLOADED"]
    eval_events = [item for item in items if item["action"] == "COMPLIANCE_EVALUATION"]
    assert len(upload_events) == 1
    assert upload_events[0]["performed_by"] == "ana.rbac"
    assert upload_events[0]["details"]["actor_role"] == "ANALISTA"

    # Ha uma avaliacao explicita (adm.rbac) e uma disparada pelo worker (propaga ana.rbac)
    assert len(eval_events) == 2
    by_trigger = {e["details"].get("trigger"): e for e in eval_events}
    assert by_trigger[None]["performed_by"] == "adm.rbac"
    assert by_trigger["CELERY_WORKER"]["performed_by"] == "ana.rbac"

    # 5. Upload via chave de servico grava performed_by="service"
    up_svc = client.post(
        f"{settings.API_V1_STR}/documents/upload?async_process=false",
        files={"file": ("cnd_svc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"X-API-Key": settings.API_KEY},
    )
    assert up_svc.status_code == 201
    svc_id = up_svc.json()["id"]
    svc_audit = (
        db_session.query(AuditLog).filter_by(entity_id=svc_id, action="DOCUMENT_UPLOADED").one()
    )
    assert svc_audit.performed_by == "service"
    assert svc_audit.details["actor_role"] == "SERVICE"
    assert db_session.get(Document, svc_id) is not None


@pytest.mark.parametrize("environment", ["development", "test"])
def test_environment_alone_does_not_grant_anonymous_access(client, monkeypatch, environment):
    """Antes, ENVIRONMENT=development/test abria a API sem chave; agora so o opt-in abre."""
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    response = client.get(f"{settings.API_V1_STR}/compliance/rules")
    assert response.status_code == 401


def test_explicit_opt_in_allows_anonymous_access(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_ACCESS", True)
    assert client.get(f"{settings.API_V1_STR}/compliance/rules").status_code == 200


def test_opt_in_does_not_bypass_an_invalid_key(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_ACCESS", True)
    response = client.get(
        f"{settings.API_V1_STR}/compliance/rules", headers={"X-API-Key": "chave-invalida"}
    )
    assert response.status_code == 401


def test_health_stays_public(client):
    assert client.get(f"{settings.API_V1_STR}/health").status_code == 200

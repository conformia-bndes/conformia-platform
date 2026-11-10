#!/usr/bin/env python3
"""Teste de fumaça: upload -> fila -> worker -> laudo de conformidade -> revisao humana.

Usa apenas a biblioteca padrao. Gera o proprio PDF, entao nao depende de fixtures.

Execucao (a partir da raiz do repositorio):
    make smoke
ou diretamente:
    docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
        python scripts/smoke_test.py
ou no host (sem Docker exec):
    API_URL=http://localhost:8000 python3 backend/scripts/smoke_test.py

Preparacao de analistas de teste no .env (usado pelo CI e pelo Makefile):
    python3 backend/scripts/smoke_test.py --setup-env .env

Variaveis: API_URL (padrao http://localhost:8000), API_KEY (opcional em desenvolvimento),
SMOKE_MAKER_KEY e SMOKE_CHECKER_KEY (chaves pessoais de dois usuarios ANALISTA distintos),
SMOKE_TIMEOUT (segundos por etapa, padrao 120).

Codigo de saida 0 = ambiente, fila, motor de conformidade e revisao humana funcionando;
qualquer outro valor = falha.
"""

import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
import urllib.error
import urllib.request
import uuid

PBKDF2_ITERATIONS = 200_000

SMOKE_CND_LINES = [
    "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA",
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E A DIVIDA ATIVA DA UNIAO",
    "CNPJ: 12.345.678/0001-90",
    "E certificado que nao constam pendencias.",
    "Valida ate: 31/12/2099",
]


def _load_dotenv_fallback() -> dict:
    """Le variaveis de um arquivo .env local caso nao estejam no ambiente do processo."""
    for candidate in (Path(".env"), Path(__file__).resolve().parents[2] / ".env"):
        if candidate.is_file():
            values = {}
            for raw in candidate.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
            return values
    return {}


_DOTENV = _load_dotenv_fallback()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name) or _DOTENV.get(name, default)


API_URL = _env("API_URL", "http://localhost:8000").rstrip("/")
API_KEY = _env("API_KEY", "")
SMOKE_MAKER_KEY = _env("SMOKE_MAKER_KEY", "")
SMOKE_CHECKER_KEY = _env("SMOKE_CHECKER_KEY", "")
TIMEOUT = int(_env("SMOKE_TIMEOUT", "120"))
API = f"{API_URL}/api/v1"


def log(msg: str) -> None:
    print(f"[smoke] {msg}", flush=True)


def fail(msg: str) -> None:
    print(f"[smoke] FALHA: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def build_smoke_user(user_id: str, role: str = "ANALISTA") -> tuple:
    """Gera (chave_pessoal, entrada_api_users) com PBKDF2-HMAC-SHA256 usando apenas a stdlib."""
    secret = secrets.token_urlsafe(32)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    entry = {
        "user_id": user_id,
        "role": role,
        "key_hash": f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}",
    }
    return f"{user_id}:{secret}", entry


def setup_env_file(env_path: Path) -> None:
    """Garante que o arquivo .env possua dois usuarios ANALISTA de teste para o smoke."""
    if not env_path.is_file():
        fail(f"arquivo {env_path} nao encontrado; execute bash scripts/setup-env.sh antes.")

    lines = env_path.read_text(encoding="utf-8").splitlines()
    existing = {}
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, v = stripped.split("=", 1)
            existing[k.strip()] = v.strip()

    try:
        users = json.loads(existing.get("API_USERS", "[]") or "[]")
    except json.JSONDecodeError:
        users = []

    user_ids = {u.get("user_id") for u in users if isinstance(u, dict)}
    if (
        existing.get("SMOKE_MAKER_KEY")
        and existing.get("SMOKE_CHECKER_KEY")
        and {"smoke.maker", "smoke.checker"}.issubset(user_ids)
    ):
        return

    maker_key, maker_entry = build_smoke_user("smoke.maker", "ANALISTA")
    checker_key, checker_entry = build_smoke_user("smoke.checker", "ANALISTA")
    users = [
        u
        for u in users
        if isinstance(u, dict) and u.get("user_id") not in ("smoke.maker", "smoke.checker")
    ]
    users.extend([maker_entry, checker_entry])
    api_users_json = json.dumps(users, separators=(",", ":"))

    new_lines = []
    replaced_api_users = False
    for line in lines:
        if line.startswith("API_USERS="):
            new_lines.append(f"API_USERS={api_users_json}")
            replaced_api_users = True
        elif line.startswith("SMOKE_MAKER_KEY=") or line.startswith("SMOKE_CHECKER_KEY="):
            continue
        else:
            new_lines.append(line)

    if not replaced_api_users:
        new_lines.append(f"API_USERS={api_users_json}")
    new_lines.append(f"SMOKE_MAKER_KEY={maker_key}")
    new_lines.append(f"SMOKE_CHECKER_KEY={checker_key}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def request(method: str, url: str, body: bytes = None, headers: dict = None):
    headers = dict(headers or {})
    if API_KEY and "X-API-Key" not in headers:
        headers["X-API-Key"] = API_KEY
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return exc.code, {"error": detail}
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"error": str(exc)}


def json_request(method: str, url: str, payload: dict, api_key: str = None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    data = json.dumps(payload).encode("utf-8")
    return request(method, url, body=data, headers=headers)


def build_pdf(text_lines) -> bytes:
    """Monta um PDF de 1 pagina com camada de texto (sem dependencias)."""
    stream = "BT /F1 12 Tf 72 720 Td 14 TL " + " T* ".join(f"({t}) Tj" for t in text_lines) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
    xref_at = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    )
    return out


def multipart(filename: str, content: bytes):
    boundary = uuid.uuid4().hex
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        ).encode()
        + content
        + f"\r\n--{boundary}--\r\n".encode()
    )
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def wait_until(label: str, check, timeout: int = TIMEOUT, interval: float = 2.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        done, last = check()
        if done:
            return last
        time.sleep(interval)
    fail(f"timeout ({timeout}s) aguardando: {label}. Ultimo estado: {last}")


def main(argv: list = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) == 2 and argv[0] == "--setup-env":
        setup_env_file(Path(argv[1]))
        return
    if argv:
        fail(f"argumentos invalidos: {argv}")

    log(f"API: {API_URL}")

    # 1) API saudavel (Postgres + Redis + MinIO)
    def health():
        code, data = request("GET", f"{API}/health")
        return (code == 200 and data.get("status") == "healthy"), data

    health_data = wait_until("API saudavel (/api/v1/health)", health)
    log(f"1/6 health OK: {health_data.get('services')}")

    # 2) Upload despacha a tarefa
    pdf = build_pdf(SMOKE_CND_LINES)
    body, headers = multipart("smoke_test.pdf", pdf)
    code, up = request("POST", f"{API}/documents/upload", body, headers)
    if code != 201:
        fail(f"upload retornou HTTP {code}: {up}")
    doc_id, task_id = up.get("id"), up.get("task_id")
    if not task_id:
        fail(f"upload nao devolveu task_id (processou fora da fila?): {up}")
    log(f"2/6 upload OK: document_id={doc_id} task_id={task_id}")

    # 3) Estado da tarefa evolui ate SUCCESS (so ocorre se o worker consumiu a fila)
    seen = []

    def task_state():
        code, data = request("GET", f"{API}/documents/tasks/{task_id}")
        state = data.get("state") if code == 200 else f"HTTP {code}"
        if not seen or seen[-1] != state:
            seen.append(state)
            log(f"     estado da tarefa: {state}")
        if state in ("FAILURE", "REVOKED"):
            fail(f"tarefa terminou em {state}: {data.get('error', data)}")
        return state == "SUCCESS", data

    result = wait_until("tarefa SUCCESS (worker consumindo a fila)", task_state)
    log(f"3/6 tarefa concluida pelo worker: {result.get('result')}")

    # 4) Estado do documento persistido pelo worker
    code, doc = request("GET", f"{API}/documents/{doc_id}")
    if code != 200 or doc.get("status") != "COMPLETED":
        fail(f"documento nao ficou COMPLETED: HTTP {code} {doc}")
    log(f"4/6 documento COMPLETED (paginas: {(doc.get('metadata') or {}).get('total_pages')})")

    # 5) Laudo de conformidade persistido (/api/v1/compliance/results/{doc_id})
    code, report = request("GET", f"{API}/compliance/results/{doc_id}")
    if code != 200:
        fail(f"consulta ao laudo retornou HTTP {code}: {report}")
    overall_status = report.get("overall_status")
    evaluated_rules = report.get("evaluated_rules", 0)
    checks = report.get("checks") or []
    if report.get("document_id") != doc_id or overall_status != "COMPLIANT" or evaluated_rules < 1:
        fail(f"laudo de conformidade inesperado: {report}")
    if not any(
        c.get("rule_id") == "RULE-BNDES-001" and c.get("status") == "COMPLIANT" for c in checks
    ):
        fail(f"regra RULE-BNDES-001 nao consta como COMPLIANT no laudo: {checks}")
    log(
        f"5/6 laudo de conformidade OK: overall_status={overall_status} "
        f"(regras avaliadas: {evaluated_rules})"
    )

    # 6) Revisao humana Maker-Checker por dois usuarios de teste (proposta + confirmacao)
    maker_key = _env("SMOKE_MAKER_KEY", "")
    checker_key = _env("SMOKE_CHECKER_KEY", "")
    if not maker_key or not checker_key:
        fail(
            "SMOKE_MAKER_KEY e SMOKE_CHECKER_KEY ausentes; "
            "rode 'python3 backend/scripts/smoke_test.py --setup-env .env' antes de subir a stack."
        )

    code, proposal = json_request(
        "POST",
        f"{API}/compliance/reviews/{doc_id}",
        {
            "decision": "APPROVE",
            "justification": "Smoke test: validade e CNPJ da CND conferidos contra o documento.",
        },
        api_key=maker_key,
    )
    if code != 201 or proposal.get("event_type") != "PROPOSED":
        fail(f"proposta de revisao (Maker) falhou com HTTP {code}: {proposal}")
    proposal_id = proposal.get("id")

    # Segregacao de funcoes: o proprio autor nao pode confirmar a proposta
    self_code, _ = json_request(
        "POST",
        f"{API}/compliance/reviews/{doc_id}/{proposal_id}/confirm",
        {"comment": "Tentativa de autoconfirmacao no smoke."},
        api_key=maker_key,
    )
    if self_code != 403:
        fail(f"segregacao Maker-Checker violada: autoconfirmacao retornou HTTP {self_code}")

    code, confirmed = json_request(
        "POST",
        f"{API}/compliance/reviews/{doc_id}/{proposal_id}/confirm",
        {"comment": "Smoke test: proposta conferida e confirmada por segundo analista."},
        api_key=checker_key,
    )
    if code != 201 or confirmed.get("event_type") != "CONFIRMED":
        fail(f"confirmacao de revisao (Checker) falhou com HTTP {code}: {confirmed}")

    code, review_state = request("GET", f"{API}/compliance/reviews/{doc_id}")
    if (
        code != 200
        or review_state.get("state") != "FINAL"
        or review_state.get("final_decision") != "APPROVE"
    ):
        fail(f"estado final da revisao inesperado: HTTP {code} {review_state}")
    log(
        f"6/6 revisao humana OK: state={review_state.get('state')} "
        f"decision={review_state.get('final_decision')} "
        f"(maker={proposal.get('actor_id')}, checker={confirmed.get('actor_id')})"
    )

    log(
        "OK - ambiente sobe, processa pela fila, gera laudo e conclui revisao Maker-Checker. "
        "Estados observados: " + " -> ".join(seen)
    )


if __name__ == "__main__":
    main()

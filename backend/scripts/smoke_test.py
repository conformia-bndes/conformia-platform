#!/usr/bin/env python3
"""Teste de fumaça: upload -> fila (Redis) -> worker (Celery) -> estado consultavel.

Usa apenas a biblioteca padrao. Gera o proprio PDF, entao nao depende de fixtures.

Execucao (a partir da raiz do repositorio):
    make smoke
ou diretamente:
    docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
        python scripts/smoke_test.py
ou no host (sem Docker exec):
    API_URL=http://localhost:8000 python3 backend/scripts/smoke_test.py

Variaveis: API_URL (padrao http://localhost:8000), API_KEY (opcional em desenvolvimento),
SMOKE_TIMEOUT (segundos por etapa, padrao 120).

Codigo de saida 0 = ambiente e fila funcionando; qualquer outro valor = falha.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")
TIMEOUT = int(os.environ.get("SMOKE_TIMEOUT", "120"))
API = f"{API_URL}/api/v1"


def log(msg: str) -> None:
    print(f"[smoke] {msg}", flush=True)


def fail(msg: str) -> None:
    print(f"[smoke] FALHA: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def request(method: str, url: str, body: bytes = None, headers: dict = None):
    headers = dict(headers or {})
    if API_KEY:
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


def main() -> None:
    log(f"API: {API_URL}")

    # 1) API saudavel (Postgres + Redis + MinIO)
    def health():
        code, data = request("GET", f"{API}/health")
        return (code == 200 and data.get("status") == "healthy"), data

    health_data = wait_until("API saudavel (/api/v1/health)", health)
    log(f"1/4 health OK: {health_data.get('services')}")

    # 2) Upload despacha a tarefa
    pdf = build_pdf(["CERTIDAO DE TESTE - SMOKE", "Documento sintetico para validar a fila."])
    body, headers = multipart("smoke_test.pdf", pdf)
    code, up = request("POST", f"{API}/documents/upload", body, headers)
    if code != 201:
        fail(f"upload retornou HTTP {code}: {up}")
    doc_id, task_id = up.get("id"), up.get("task_id")
    if not task_id:
        fail(f"upload nao devolveu task_id (processou fora da fila?): {up}")
    log(f"2/4 upload OK: document_id={doc_id} task_id={task_id}")

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
    log(f"3/4 tarefa concluida pelo worker: {result.get('result')}")

    # 4) Estado do documento persistido pelo worker
    code, doc = request("GET", f"{API}/documents/{doc_id}")
    if code != 200 or doc.get("status") != "COMPLETED":
        fail(f"documento nao ficou COMPLETED: HTTP {code} {doc}")
    log(f"4/4 documento COMPLETED (paginas: {(doc.get('metadata') or {}).get('total_pages')})")

    log("OK - ambiente sobe e processa pela fila. Estados observados: " + " -> ".join(seen))


if __name__ == "__main__":
    main()

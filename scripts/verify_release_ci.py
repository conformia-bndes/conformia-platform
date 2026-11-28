#!/usr/bin/env python3
"""Verifica na API do GitHub se o check 'CI OK' esta verde para o SHA exato de uma tag de release.

Usado pelo workflow `.github/workflows/cd.yml` (Issue #171 / AUD-17b) para impedir publicacao de
imagens de release quando o CI daquele commit exato nao concluiu com sucesso.

Usa apenas a biblioteca padrao do Python.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Tuple

FAILED_CONCLUSIONS = frozenset(
    {"failure", "cancelled", "timed_out", "action_required", "stale", "startup_failure"}
)


def fetch_check_runs(
    repo: str,
    sha: str,
    check_name: str,
    token: str,
    api_url: str = "https://api.github.com",
) -> List[Dict[str, Any]]:
    """Consulta os check-runs do commit exato na API REST do GitHub."""
    query = urllib.parse.urlencode({"check_name": check_name, "per_page": "100"})
    url = f"{api_url.rstrip('/')}/repos/{repo}/commits/{sha}/check-runs?{query}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "conformia-release-ci-gate",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return list(payload.get("check_runs") or [])


def evaluate_check_runs(check_runs: List[Dict[str, Any]], check_name: str) -> Tuple[str, str]:
    """
    Avalia os check-runs retornados para o SHA da tag.
    Retorna `(estado, mensagem)` onde estado e:
    - "PASS": ha execucao concluida com `conclusion == "success"` e nenhuma mais recente falhou.
    - "PENDING": existe execucao `queued` ou `in_progress` aguardando conclusao.
    - "FAIL": nenhuma execucao encontrada ou a mais recente concluiu sem sucesso.
    """
    matching = [r for r in check_runs if r.get("name") == check_name]
    if not matching:
        return "FAIL", f"Nenhum check-run '{check_name}' encontrado para este SHA."

    # Ordena do mais recente para o mais antigo por id (monotonico no GitHub).
    matching.sort(key=lambda r: int(r.get("id") or 0), reverse=True)
    latest = matching[0]
    status = str(latest.get("status") or "")
    conclusion = str(latest.get("conclusion") or "")

    if status == "completed" and conclusion == "success":
        return "PASS", f"Check '{check_name}' aprovado (id={latest.get('id')}, conclusion=success)."
    if status in {"queued", "in_progress", "waiting", "pending"}:
        return (
            "PENDING",
            f"Check '{check_name}' em andamento (id={latest.get('id')}, status={status}).",
        )
    if conclusion in FAILED_CONCLUSIONS or status == "completed":
        return (
            "FAIL",
            f"Check '{check_name}' nao aprovado (id={latest.get('id')}, "
            f"status={status}, conclusion={conclusion or 'none'}).",
        )
    return "FAIL", f"Estado inesperado para check '{check_name}': status={status}."


def verify_sha_ci(
    repo: str,
    sha: str,
    check_name: str = "CI OK",
    token: str = "",
    wait_seconds: int = 0,
    poll_interval: int = 20,
    fetcher: Callable[[str, str, str, str], List[Dict[str, Any]]] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> Tuple[bool, str]:
    """
    Aguarda ate `wait_seconds` enquanto o check estiver em andamento e decide se o SHA da tag
    pode ser publicado. Falha imediatamente se nao houver check verde ou se o check falhar.
    """
    fetch = fetcher or fetch_check_runs
    deadline = time.monotonic() + max(0, wait_seconds)
    last_message = f"Check '{check_name}' nao confirmado para {sha}."

    while True:
        try:
            runs = fetch(repo, sha, check_name, token)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return False, f"Erro ao consultar API de checks do GitHub para {sha}: {exc}"

        state, message = evaluate_check_runs(runs, check_name)
        last_message = message
        if state == "PASS":
            return True, message
        if state == "FAIL":
            # Quando o release-please roda no mesmo push para main que dispara o CI, o check-run
            # 'CI OK' pode ainda nao ter sido criado nos primeiros segundos. So aguarda se
            # wait_seconds > 0 e ainda nao existe nenhum check concluido com falha.
            has_completed_failure = any(
                r.get("name") == check_name and r.get("status") == "completed" for r in runs
            )
            if has_completed_failure or time.monotonic() >= deadline:
                return False, message
        elif time.monotonic() >= deadline:
            return False, f"Timeout aguardando conclusao do CI para {sha}: {message}"

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False, last_message
        sleeper(min(poll_interval, remaining))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True, help="Repositorio owner/name")
    parser.add_argument("--sha", required=True, help="SHA exato do commit apontado pela tag")
    parser.add_argument("--check-name", default="CI OK", help="Nome do check obrigatorio")
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        help="Tempo maximo em segundos para aguardar CI em execucao (padrao: 0)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=20,
        help="Intervalo entre consultas em segundos (padrao: 20)",
    )
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    ok, message = verify_sha_ci(
        repo=args.repo,
        sha=args.sha,
        check_name=args.check_name,
        token=token,
        wait_seconds=args.wait_seconds,
        poll_interval=args.poll_interval,
    )
    if ok:
        print(f"[cd-ci-gate] OK ({args.sha[:12]}): {message}")
        return 0
    print(f"::error::[cd-ci-gate] BLOQUEADO ({args.sha[:12]}): {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

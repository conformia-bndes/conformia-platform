"""
Hook do MkDocs que gera a pagina "Relatorios de Qualidade" a partir dos artefatos do CI.

O CI de `main` publica, a cada execucao, relatorios de testes (JUnit), cobertura (Cobertura XML),
evals, fuzzing e auditorias de dependencias. O workflow `docs.yml` baixa esses artefatos para a
pasta `reports/` (ou a indicada em CONFORMIA_REPORTS_DIR) antes de gerar o site, e este hook
transforma os arquivos em uma pagina virtual (nada e gravado em `docs/`).

Sem relatorios (build local ou de PR), a pagina explica como gera-los e o build nao falha: os
relatorios sao uma vitrine do estado de `main`, nao um criterio de aprovacao.

Metadados opcionais, passados pelo workflow: REPORT_COMMIT, REPORT_RUN_URL e REPORT_DATE.
So usa a biblioteca padrao.
"""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

from mkdocs.structure.files import File, Files

PAGE_PATH = "relatorios/index.md"
LOWEST_COVERAGE_ROWS = 10


def _reports_dir() -> Path:
    return Path(os.environ.get("CONFORMIA_REPORTS_DIR", "reports"))


def _find(root: Path, name: str) -> Optional[Path]:
    """Primeiro arquivo com esse nome em qualquer subpasta (cada artefato vem em uma pasta)."""
    if not root.is_dir():
        return None
    return next(iter(sorted(root.rglob(name))), None)


def _read_json(path: Optional[Path]) -> Any:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_xml(path: Optional[Path]) -> Optional[ET.Element]:
    """
    Le um XML de relatorio (JUnit ou Cobertura). Esses arquivos nunca declaram DOCTYPE nem
    entidades; se aparecerem, o arquivo e recusado antes da interpretacao, o que elimina
    ataques de entidades externas e de expansao de entidades sem exigir dependencia extra.
    """
    if path is None:
        return None
    try:
        content = path.read_bytes()
        if b"<!DOCTYPE" in content or b"<!ENTITY" in content:
            return None
        return ET.fromstring(content)  # noqa: S314 - entrada validada acima
    except (OSError, ET.ParseError):
        return None


def _badge(ok: bool) -> str:
    return "Aprovado" if ok else "Falhou"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def _seconds(value: float) -> str:
    return f"{value:.1f} s".replace(".", ",")


def _unavailable(title: str) -> str:
    return f"### {title}\n\nRelatório indisponível nesta publicação.\n"


def _junit_section(title: str, path: Optional[Path]) -> str:
    root = _read_xml(path)
    if root is None:
        return _unavailable(title)
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    seconds = sum(float(s.get("time", 0)) for s in suites)
    passed = total - failures - skipped
    slowest = sorted(
        (
            (float(c.get("time", 0)), f"{c.get('classname', '')}::{c.get('name', '')}")
            for c in root.iter("testcase")
        ),
        reverse=True,
    )[:5]
    rows = "\n".join(f"| `{name}` | {_seconds(t)} |" for t, name in slowest)
    slowest_block = (
        f"\nTestes mais lentos:\n\n| Teste | Tempo |\n| :-- | --: |\n{rows}\n"
        if slowest and slowest[0][0] >= 0.1
        else ""
    )
    return (
        f"### {title}\n\n"
        f"| Resultado | Testes | Passaram | Pulados | Falharam | Duração |\n"
        f"| :-- | --: | --: | --: | --: | --: |\n"
        f"| **{_badge(failures == 0)}** | {total} | {passed} | {skipped} | {failures} | "
        f"{_seconds(seconds)} |\n{slowest_block}"
    )


def _coverage_section(path: Optional[Path]) -> str:
    root = _read_xml(path)
    title = "Cobertura de testes do backend"
    if root is None:
        return _unavailable(title)
    line_rate = float(root.get("line-rate", 0))
    branch_rate = float(root.get("branch-rate", 0))
    branches_measured = int(root.get("branches-valid", 0)) > 0
    branches = _pct(branch_rate) if branches_measured else "não medido"
    files: list[tuple[float, str, int, int]] = []
    for cls in root.iter("class"):
        lines = [ln for ln in cls.iter("line")]
        if not lines:
            continue
        covered = sum(1 for ln in lines if int(ln.get("hits", 0)) > 0)
        files.append((covered / len(lines), cls.get("filename", "?"), covered, len(lines)))
    lowest = sorted(files)[:LOWEST_COVERAGE_ROWS]
    rows = "\n".join(
        f"| `{name}` | {_pct(rate)} | {cov}/{tot} |" for rate, name, cov, tot in lowest
    )
    return (
        f"### {title}\n\n"
        f"| Linhas | Ramos | Arquivos medidos |\n| --: | --: | --: |\n"
        f"| **{_pct(line_rate)}** | {branches} | {len(files)} |\n\n"
        f"Arquivos com menor cobertura:\n\n"
        f"| Arquivo | Cobertura | Linhas cobertas |\n| :-- | --: | --: |\n{rows}\n"
    )


def _evals_section(path: Optional[Path]) -> str:
    title = "Benchmark de regras (evals)"
    data = _read_json(path)
    if not isinstance(data, dict) or "metrics" not in data:
        return _unavailable(title)
    m = data["metrics"]
    return (
        f"### {title}\n\n"
        f"| Resultado | Verificações | Corretas | Falsos positivos | Acurácia | Mínimo |\n"
        f"| :-- | --: | --: | --: | --: | --: |\n"
        f"| **{_badge(bool(data.get('passed')))}** | {m.get('total_checks')} | "
        f"{m.get('passed_checks')} | {m.get('false_positives')} | "
        f"{str(m.get('accuracy')).replace('.', ',')}% | "
        f"{str(data.get('accuracy_threshold')).replace('.', ',')}% |\n\n"
        f"Hash do checklist: `{str(data.get('rules_sha256', ''))[:12]}`.\n"
    )


def _fuzz_section(path: Optional[Path]) -> str:
    title = "Fuzzing do motor de regras (Atheris)"
    if path is None:
        return _unavailable(title)
    text = path.read_text(encoding="utf-8", errors="replace")
    runs = re.search(r"Done (\d+) runs in (\d+) second", text)
    rate = re.search(r"average_exec_per_sec:\s*(\d+)", text)
    rss = re.search(r"peak_rss_mb:\s*(\d+)", text)
    crashed = bool(re.search(r"(Test unit written|ERROR: libFuzzer|AssertionError)", text))
    if not runs:
        return _unavailable(title)
    return (
        f"### {title}\n\n"
        f"| Resultado | Entradas testadas | Duração | Execuções/s | Memória (pico) |\n"
        f"| :-- | --: | --: | --: | --: |\n"
        f"| **{_badge(not crashed)}** | {int(runs.group(1)):,} | {runs.group(2)} s | "
        f"{rate.group(1) if rate else '?'} | {rss.group(1) + ' MB' if rss else '?'} |\n".replace(
            ",", "."
        )
    )


def _audit_section(pip_path: Optional[Path], npm_path: Optional[Path]) -> str:
    title = "Auditoria de dependências"
    pip = _read_json(pip_path)
    npm = _read_json(npm_path)
    rows = []
    if isinstance(pip, dict):
        vulns = sum(len(d.get("vulns", [])) for d in pip.get("dependencies", []))
        rows.append(f"| Python (`uv.lock`) | **{_badge(vulns == 0)}** | {vulns} |")
    if isinstance(npm, dict):
        meta = npm.get("metadata", {}).get("vulnerabilities", {})
        total = int(meta.get("total", sum(v for v in meta.values() if isinstance(v, int))))
        rows.append(f"| Frontend (`package-lock.json`) | **{_badge(total == 0)}** | {total} |")
    if not rows:
        return _unavailable(title)
    return (
        f"### {title}\n\n| Ecossistema | Resultado | Vulnerabilidades |\n| :-- | :-- | --: |\n"
        + "\n".join(rows)
        + "\n"
    )


def build_page(root: Path) -> str:
    commit = os.environ.get("REPORT_COMMIT", "")
    run_url = os.environ.get("REPORT_RUN_URL", "")
    date = os.environ.get("REPORT_DATE", "")
    available = root.is_dir() and any(root.rglob("*"))

    lines = ["# Relatórios de Qualidade", ""]
    if not available:
        lines += [
            "Os relatórios são gerados pelo CI e publicados junto com o site a partir da branch",
            "`main`. Esta versão da documentação foi gerada sem eles.",
            "",
            "Para gerá-los localmente:",
            "",
            "```bash",
            "make reports   # testes, cobertura, evals e auditorias em reports/",
            "make docs      # o site passa a exibir os relatórios",
            "```",
        ]
        return "\n".join(lines) + "\n"

    origin = []
    if commit:
        origin.append(f"commit `{commit[:7]}`")
    if date:
        origin.append(date)
    if run_url:
        origin.append(f"[execução do CI]({run_url})")
    lines += [
        "Resultados da última execução do CI na branch `main`"
        + (f" ({', '.join(origin)})." if origin else "."),
        "Os arquivos completos ficam como artefatos da execução, por 30 dias.",
        "",
    ]
    sections = [
        _junit_section("Testes do backend", _find(root, "junit-backend.xml")),
        _coverage_section(_find(root, "coverage.xml")),
        _evals_section(_find(root, "eval_report.json")),
        _fuzz_section(_find(root, "fuzz.txt")),
        _junit_section("Testes do frontend", _find(root, "junit-frontend.xml")),
        _audit_section(_find(root, "pip-audit.json"), _find(root, "npm-audit.json")),
    ]
    lines += ["\n".join(sections)]
    return "\n".join(lines) + "\n"


def on_files(files: Files, config) -> Files:
    page = File.generated(config, PAGE_PATH, content=build_page(_reports_dir()))
    files.append(page)
    return files

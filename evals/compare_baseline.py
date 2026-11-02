"""
Gate de regressao dos evals: compara o relatorio de uma execucao com a linha de base versionada.

A linha de base (`evals/baseline.json`) e o ultimo resultado aceito do benchmark de regras e so
muda por PR revisado (`make eval-baseline`). O gate falha quando:

- ha falso positivo (nenhuma tolerancia);
- a acuracia cai abaixo da linha de base;
- uma verificacao que passava na linha de base passa a falhar (regressao pontual, mesmo que a
  acuracia geral se mantenha por compensacao com casos novos).

Verificacoes novas, e mudancas no checklist ou no dataset, nao reprovam por si: o resumo
informa que a linha de base deve ser atualizada quando elas mudarem o resultado.

Uso:
    python evals/compare_baseline.py REPORT.json            # compara com a linha de base
    python evals/compare_baseline.py REPORT.json --update   # grava a nova linha de base

Se GITHUB_STEP_SUMMARY existir, o resumo em Markdown tambem e gravado nele.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

BASELINE_PATH = Path(__file__).resolve().parent / "baseline.json"


def _key(check: Dict[str, Any]) -> str:
    return f"{check['case_id']}|{check['rule_id']}"


def build_baseline(report: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai da execucao o que precisa ser versionado como linha de base."""
    metrics = report["metrics"]
    return {
        "accuracy": metrics["accuracy"],
        "false_positives": metrics["false_positives"],
        "total_checks": metrics["total_checks"],
        "rules_sha256": report.get("rules_sha256"),
        "datasets_sha256": report.get("datasets_sha256"),
        "checks": {_key(c): c["outcome"] for c in report["checks"]},
    }


def compare(report: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Compara uma execucao com a linha de base e devolve achados e veredito."""
    metrics = report["metrics"]
    current = {_key(c): c["outcome"] for c in report["checks"]}
    base_checks: Dict[str, str] = baseline.get("checks", {})

    errors: List[str] = []
    if metrics["false_positives"] > 0:
        errors.append(f"{metrics['false_positives']} falso(s) positivo(s): tolerancia zero.")
    if metrics["accuracy"] < baseline["accuracy"]:
        errors.append(
            f"Acuracia {metrics['accuracy']}% abaixo da linha de base ({baseline['accuracy']}%)."
        )
    regressions = sorted(
        key for key, outcome in base_checks.items()
        if outcome == "PASS" and current.get(key, "MISSING") != "PASS"
    )  # fmt: skip
    for key in regressions:
        state = current.get(key, "removida")
        errors.append(f"Regressao: {key} passava na linha de base e agora esta {state}.")

    new_checks = sorted(set(current) - set(base_checks))
    fixed = sorted(k for k, o in current.items() if o == "PASS" and base_checks.get(k) == "FAIL")
    notes: List[str] = []
    if report.get("rules_sha256") != baseline.get("rules_sha256"):
        notes.append("O checklist de regras mudou desde a linha de base.")
    if report.get("datasets_sha256") != baseline.get("datasets_sha256"):
        notes.append("O dataset de evals mudou desde a linha de base.")
    if new_checks or fixed or notes:
        notes.append("Se a mudanca e intencional, atualize a linha de base: `make eval-baseline`.")

    return {
        "ok": not errors,
        "errors": errors,
        "new_checks": new_checks,
        "fixed": fixed,
        "notes": notes,
        "accuracy": metrics["accuracy"],
        "baseline_accuracy": baseline["accuracy"],
    }


def render_markdown(result: Dict[str, Any]) -> str:
    status = "Aprovado" if result["ok"] else "Regressao detectada"
    lines = [
        "### Gate de regressao dos evals",
        "",
        "| Resultado | Acuracia | Linha de base | Verificacoes novas | Corrigidas |",
        "| :-- | --: | --: | --: | --: |",
        f"| **{status}** | {result['accuracy']}% | {result['baseline_accuracy']}% | "
        f"{len(result['new_checks'])} | {len(result['fixed'])} |",
        "",
    ]
    lines += [f"- {e}" for e in result["errors"]]
    lines += [f"- {n}" for n in result["notes"]]
    return "\n".join(lines) + "\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("report", help="JSON gerado por eval_pipeline.py --json-report")
    parser.add_argument("--update", action="store_true", help="grava a nova linha de base")
    parser.add_argument("--baseline", default=str(BASELINE_PATH))
    args = parser.parse_args(argv)

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    baseline_path = Path(args.baseline)

    if args.update:
        if report["metrics"]["false_positives"] > 0:
            print("Recusado: a linha de base nao pode conter falsos positivos.", file=sys.stderr)
            return 1
        baseline_path.write_text(
            json.dumps(build_baseline(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Linha de base gravada em {baseline_path}")
        return 0

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    result = compare(report, baseline)
    summary = render_markdown(result)
    print(summary)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(summary)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""
Verificacao estrutural dos workflows do GitHub Actions (.github/workflows/*.yml).

Complementa o actionlint com as checagens que, se falham, derrubam o CI inteiro sem criar jobs
(o que ja aconteceu quando um workflow reutilizavel perdeu o cabecalho):

- o YAML e valido e tem `jobs`;
- todo job referenciado em `needs` existe no mesmo arquivo;
- todo `uses: ./.github/workflows/x.yml` aponta para um arquivo que existe e declara
  `workflow_call`;
- todo `with:` de uma chamada local usa apenas inputs declarados pelo workflow chamado e inclui
  os obrigatorios.

Uso: python scripts/check_workflows.py [pasta]   (padrao: .github/workflows)
Sai com codigo 1 e lista os problemas se algo estiver errado.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

LOCAL_PREFIX = "./.github/workflows/"


def _triggers(doc: Dict[Any, Any]) -> Dict[str, Any]:
    # YAML 1.1 interpreta a chave `on` como o booleano True.
    value = doc.get("on", doc.get(True)) or {}
    if isinstance(value, str):
        return {value: None}
    if isinstance(value, list):
        return {name: None for name in value}
    return value


def check(folder: Path) -> List[str]:
    problems: List[str] = []
    docs: Dict[str, Dict[Any, Any]] = {}

    for path in sorted(folder.glob("*.yml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            problems.append(f"{path.name}: YAML invalido ({exc})")
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict) or not doc["jobs"]:
            problems.append(f"{path.name}: sem a chave `jobs` ou sem nenhum job")
            continue
        docs[path.name] = doc

    for name, doc in docs.items():
        jobs: Dict[str, Any] = doc["jobs"]
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                problems.append(f"{name}: job `{job_id}` invalido")
                continue
            needs = job.get("needs", [])
            for needed in [needs] if isinstance(needs, str) else needs:
                if needed not in jobs:
                    problems.append(f"{name}: job `{job_id}` depende de `{needed}`, que nao existe")

            uses = job.get("uses")
            if not isinstance(uses, str) or not uses.startswith(LOCAL_PREFIX):
                continue
            target = uses[len(LOCAL_PREFIX) :]
            called = docs.get(target)
            if called is None:
                problems.append(f"{name}: job `{job_id}` usa {uses}, que nao existe ou e invalido")
                continue
            call = _triggers(called).get("workflow_call")
            if "workflow_call" not in _triggers(called):
                problems.append(f"{name}: {target} nao declara `workflow_call`")
                continue
            declared: Dict[str, Any] = (call or {}).get("inputs", {}) or {}
            given: Dict[str, Any] = job.get("with", {}) or {}
            for key in given:
                if key not in declared:
                    problems.append(f"{name}: job `{job_id}` passa `{key}`, ausente em {target}")
            for key, spec in declared.items():
                if (spec or {}).get("required") and key not in given:
                    problems.append(f"{name}: job `{job_id}` nao passa `{key}` (obrigatorio)")

    return problems


def main(argv: List[str]) -> int:
    folder = Path(argv[1]) if len(argv) > 1 else Path(".github/workflows")
    problems = check(folder)
    for problem in problems:
        print(f"ERRO: {problem}")
    if problems:
        return 1
    print(f"Workflows em {folder}: estrutura valida.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

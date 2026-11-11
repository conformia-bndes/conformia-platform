"""Testes para configuracao da Release Candidate RC1 e relatorio de regressao (Issue #62)."""

import json
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_release_please_configured_for_rc1():
    """Garante que o release-please esta configurado para gerar a tag v1.0.0-rc.1."""
    config_path = REPO_ROOT / "release-please-config.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))

    assert data.get("include-component-in-tag") is False
    pkg = data["packages"]["."]
    assert pkg["prerelease"] is True
    assert pkg["prerelease-type"] == "rc"
    assert pkg["release-as"] == "1.0.0-rc.1"


def test_code_freeze_policy_enforced_in_pr_title_workflow():
    """Garante que o workflow pr-title.yml aplica o Code Freeze a partir de 01/12/2026."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / "pr-title.yml"
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    steps = data["jobs"]["pr-title"]["steps"]
    freeze_steps = [s for s in steps if "Code Freeze" in s.get("name", "")]
    assert len(freeze_steps) == 1
    freeze_step = freeze_steps[0]
    assert freeze_step["env"]["CODE_FREEZE_DATE"] == "2026-12-01"
    assert "feat" in freeze_step["run"]


def test_validation_report_records_complete_rc1_regression():
    """Garante que a regressao completa (pytest, vitest, evals, smoke) consta no relatorio."""
    report = (REPO_ROOT / "docs" / "planning" / "VALIDATION_REPORT.md").read_text(encoding="utf-8")
    delivery_plan = (REPO_ROOT / "docs" / "planning" / "DELIVERY_PLAN_2026_12_05.md").read_text(
        encoding="utf-8"
    )

    assert "v1.0.0-rc.1" in report
    assert "pytest" in report
    assert "vitest" in report
    assert "eval_pipeline.py" in report
    assert "smoke_test.py" in report
    assert "Code Freeze (01/12/2026)" in delivery_plan
    assert "v1.0.0-rc.1" in delivery_plan

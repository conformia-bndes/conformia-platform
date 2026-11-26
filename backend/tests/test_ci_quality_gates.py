"""Tests for CI lint scope and coverage quality gates (Issue #170)."""

from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_backend_workflow_enforces_lint_scope_and_coverage_gate():
    """Issue #170: ci-backend.yml lints backend/ docs_hooks/ evals/ scripts/ and enforces >= 70%."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / "ci-backend.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    lint_job = workflow["jobs"]["lint"]
    assert not lint_job.get("continue-on-error")
    steps_by_name = {step.get("name"): step for step in lint_job["steps"] if "name" in step}

    black_step = steps_by_name["black"]
    assert not black_step.get("continue-on-error")
    assert "backend/ docs_hooks/ evals/ scripts/" in black_step["run"]
    assert "|| true" not in black_step["run"]

    flake8_step = steps_by_name["flake8"]
    assert not flake8_step.get("continue-on-error")
    assert "backend/ docs_hooks/ evals/ scripts/" in flake8_step["run"]
    assert "--max-line-length=100" in flake8_step["run"]
    assert "|| true" not in flake8_step["run"]

    test_job = workflow["jobs"]["test"]
    assert not test_job.get("continue-on-error")
    pytest_step = next(s for s in test_job["steps"] if s.get("name") == "pytest com cobertura")
    assert not pytest_step.get("continue-on-error")
    assert "--cov=backend/app" in pytest_step["run"]
    assert "--cov-fail-under=70" in pytest_step["run"]
    assert "|| true" not in pytest_step["run"]

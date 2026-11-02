"""Testes do gate de regressao dos evals (evals/compare_baseline.py)."""

import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "compare_baseline", Path(__file__).resolve().parents[2] / "evals" / "compare_baseline.py"
)
compare_baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare_baseline)


def _report(outcomes, false_positives=0, rules="r1", datasets="d1"):
    checks = [
        {"case_id": f"C{i}", "rule_id": "R", "outcome": outcome}
        for i, outcome in enumerate(outcomes, start=1)
    ]
    passed = sum(1 for o in outcomes if o == "PASS")
    return {
        "metrics": {
            "total_checks": len(outcomes),
            "passed_checks": passed,
            "false_positives": false_positives,
            "accuracy": round(100 * passed / len(outcomes), 2),
        },
        "rules_sha256": rules,
        "datasets_sha256": datasets,
        "checks": checks,
    }


def test_same_result_passes():
    report = _report(["PASS", "PASS", "FAIL"])
    result = compare_baseline.compare(report, compare_baseline.build_baseline(report))
    assert result["ok"] and not result["errors"] and not result["notes"]


def test_accuracy_drop_and_pointwise_regression_fail():
    baseline = compare_baseline.build_baseline(_report(["PASS", "PASS", "PASS"]))
    result = compare_baseline.compare(_report(["PASS", "PASS", "FAIL"]), baseline)
    assert not result["ok"]
    assert any("Acuracia" in e for e in result["errors"])
    assert any("C3|R" in e for e in result["errors"])


def test_compensation_by_new_cases_does_not_hide_regression():
    baseline = compare_baseline.build_baseline(_report(["PASS", "FAIL"]))
    report = _report(["FAIL", "FAIL"])  # C1 regride
    report["checks"] += [{"case_id": f"N{i}", "rule_id": "R", "outcome": "PASS"} for i in range(8)]
    report["metrics"].update(total_checks=10, passed_checks=8, accuracy=80.0)
    result = compare_baseline.compare(report, baseline)
    assert not result["ok"]
    assert any("C1|R" in e for e in result["errors"])


def test_false_positive_always_fails():
    baseline = compare_baseline.build_baseline(_report(["PASS", "PASS"]))
    result = compare_baseline.compare(_report(["PASS", "PASS"], false_positives=1), baseline)
    assert not result["ok"]
    assert any("falso" in e for e in result["errors"])


def test_new_cases_and_changed_inputs_pass_with_notes():
    baseline = compare_baseline.build_baseline(_report(["PASS"]))
    report = _report(["PASS", "PASS"], rules="r2", datasets="d2")
    result = compare_baseline.compare(report, baseline)
    assert result["ok"]
    assert result["new_checks"] == ["C2|R"]
    assert any("make eval-baseline" in n for n in result["notes"])


def test_update_refuses_false_positives(tmp_path):
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(_report(["PASS"], false_positives=1)), encoding="utf-8")
    code = compare_baseline.main(
        [str(report_file), "--update", "--baseline", str(tmp_path / "baseline.json")]
    )
    assert code == 1 and not (tmp_path / "baseline.json").exists()

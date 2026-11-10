"""Tests for the extended smoke test script (Issue #57)."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.api.v1.endpoints import documents, health
from app.core.celery_app import process_document_task
from app.core.config import ApiUser, settings
from app.core.security import resolve_principal
from app.core.storage import storage_service
from app.db.models.review import ReviewEvent


def _load_smoke_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "smoke_test.py"
    spec = importlib.util.spec_from_file_location("smoke_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_setup_env_file_registers_two_analysts_and_is_idempotent(tmp_path, monkeypatch):
    smoke = _load_smoke_module()
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=segredo\nAPI_USERS=[]\n", encoding="utf-8")

    smoke.main(["--setup-env", str(env_file)])
    content = env_file.read_text(encoding="utf-8")
    kv = dict(
        line.split("=", 1)
        for line in content.splitlines()
        if line.strip() and not line.startswith("#")
    )

    assert "SMOKE_MAKER_KEY" in kv
    assert "SMOKE_CHECKER_KEY" in kv
    users = [ApiUser(**u) for u in json.loads(kv["API_USERS"])]
    assert {u.user_id for u in users} == {"smoke.maker", "smoke.checker"}
    assert all(u.role == "ANALISTA" for u in users)

    monkeypatch.setattr(settings, "API_USERS", users)
    maker = resolve_principal(kv["SMOKE_MAKER_KEY"])
    checker = resolve_principal(kv["SMOKE_CHECKER_KEY"])
    assert (maker.user_id, maker.role) == ("smoke.maker", "ANALISTA")
    assert (checker.user_id, checker.role) == ("smoke.checker", "ANALISTA")

    # Segunda chamada nao altera as chaves geradas.
    smoke.main(["--setup-env", str(env_file)])
    assert env_file.read_text(encoding="utf-8") == content


def test_extended_smoke_exercises_upload_worker_compliance_and_human_review(
    client, db_session, monkeypatch, tmp_path, capsys
):
    smoke = _load_smoke_module()
    env_file = tmp_path / ".env"
    env_file.write_text("API_USERS=[]\n", encoding="utf-8")
    smoke.setup_env_file(env_file)
    kv = dict(line.split("=", 1) for line in env_file.read_text(encoding="utf-8").splitlines())

    users = [ApiUser(**u) for u in json.loads(kv["API_USERS"])]
    monkeypatch.setattr(settings, "API_USERS", users)
    monkeypatch.setenv("SMOKE_MAKER_KEY", kv["SMOKE_MAKER_KEY"])
    monkeypatch.setenv("SMOKE_CHECKER_KEY", kv["SMOKE_CHECKER_KEY"])

    # Simula ambiente saudavel (Postgres + Redis + MinIO) e fila Celery consumida pelo worker.
    monkeypatch.setattr(storage_service, "ping", lambda: True)
    monkeypatch.setattr(
        health,
        "_redis_client",
        lambda: SimpleNamespace(ping=lambda: True),
    )
    monkeypatch.setattr(storage_service, "upload_file", lambda *a, **kw: "s3://documents/smoke")
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    task_results = {}

    def fake_delay(doc_id, file_path, object_name=None):
        res = process_document_task.run(doc_id, file_path, object_name=object_name)
        task_id = f"smoke-task-{doc_id}"
        task_results[task_id] = res
        return SimpleNamespace(id=task_id)

    def fake_async_result(task_id):
        return SimpleNamespace(
            state="SUCCESS",
            ready=lambda: True,
            successful=lambda: True,
            result=task_results.get(task_id),
        )

    monkeypatch.setattr(documents.process_document_task, "delay", fake_delay)
    monkeypatch.setattr(
        documents, "AsyncResult", lambda task_id, app=None: fake_async_result(task_id)
    )

    def client_request(method, url, body=None, headers=None):
        path = url.replace(smoke.API_URL, "")
        resp = client.request(method, path, content=body, headers=headers or {})
        return resp.status_code, resp.json()

    monkeypatch.setattr(smoke, "request", client_request)

    smoke.main([])
    output = capsys.readouterr().out
    assert "5/6 laudo de conformidade OK: overall_status=COMPLIANT" in output
    assert "6/6 revisao humana OK: state=FINAL decision=APPROVE" in output

    events = db_session.query(ReviewEvent).order_by(ReviewEvent.created_at).all()
    assert [(e.event_type, e.actor_id) for e in events] == [
        ("PROPOSED", "smoke.maker"),
        ("CONFIRMED", "smoke.checker"),
    ]


def test_smoke_fails_when_review_keys_are_missing(monkeypatch):
    smoke = _load_smoke_module()
    monkeypatch.delenv("SMOKE_MAKER_KEY", raising=False)
    monkeypatch.delenv("SMOKE_CHECKER_KEY", raising=False)
    monkeypatch.setattr(smoke, "_DOTENV", {})

    def fake_request(method, url, body=None, headers=None):
        if url.endswith("/health"):
            return 200, {"status": "healthy", "services": {"database": "healthy"}}
        if url.endswith("/documents/upload"):
            return 201, {"id": "doc-1", "task_id": "task-1"}
        if url.endswith("/documents/tasks/task-1"):
            return 200, {"state": "SUCCESS", "result": {"status": "COMPLETED"}}
        if url.endswith("/documents/doc-1"):
            return 200, {"id": "doc-1", "status": "COMPLETED", "metadata": {"total_pages": 1}}
        if url.endswith("/compliance/results/doc-1"):
            return (
                200,
                {
                    "document_id": "doc-1",
                    "overall_status": "COMPLIANT",
                    "evaluated_rules": 1,
                    "checks": [{"rule_id": "RULE-BNDES-001", "status": "COMPLIANT"}],
                },
            )
        return 404, {}

    monkeypatch.setattr(smoke, "request", fake_request)
    with pytest.raises(SystemExit) as exc:
        smoke.main([])
    assert exc.value.code == 1

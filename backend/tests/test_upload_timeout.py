"""Tests for upload deadline configuration and bounded dependency execution."""

from concurrent.futures import Future, ThreadPoolExecutor
import threading
import time

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.upload_timeout import UploadDependencyTimeout, UploadOperationRunner

VALID_SETTINGS = {
    "SECRET_KEY": "test-secret",
    "API_KEY": "test-key",
    "POSTGRES_PASSWORD": "test-password",
    "MINIO_ROOT_USER": "test-user",
    "MINIO_ROOT_PASSWORD": "test-minio-password",
}


def test_upload_timeout_defaults_to_eight_seconds(monkeypatch):
    monkeypatch.delenv("UPLOAD_TOTAL_TIMEOUT_SECONDS", raising=False)
    settings = Settings(_env_file=None, **VALID_SETTINGS)

    assert settings.UPLOAD_TOTAL_TIMEOUT_SECONDS == 8


@pytest.mark.parametrize("timeout", [0, -1, -0.1])
def test_upload_timeout_requires_positive_value(timeout):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, UPLOAD_TOTAL_TIMEOUT_SECONDS=timeout, **VALID_SETTINGS)


def test_abandoned_operation_keeps_slot_until_it_finishes():
    runner = UploadOperationRunner(max_workers=1)
    runner.start()
    entered = threading.Event()
    release = threading.Event()

    def blocked_operation(_cancellation_event):
        entered.set()
        release.wait(timeout=2)

    try:
        with pytest.raises(UploadDependencyTimeout):
            runner.run(blocked_operation, time.monotonic() + 0.05)

        assert entered.wait(timeout=1)
        assert runner.available_slots == 0

        release.set()
        deadline = time.monotonic() + 1
        while runner.available_slots == 0 and time.monotonic() < deadline:
            time.sleep(0.005)

        assert runner.available_slots == 1
    finally:
        release.set()
        runner.shutdown()


@pytest.mark.parametrize("raises", [False, True])
def test_completed_operation_releases_slot(raises):
    runner = UploadOperationRunner(max_workers=1)
    runner.start()

    def operation(_cancellation_event):
        if raises:
            raise RuntimeError("expected test failure")
        return "done"

    try:
        if raises:
            with pytest.raises(RuntimeError, match="expected test failure"):
                runner.run(operation, time.monotonic() + 1)
        else:
            assert runner.run(operation, time.monotonic() + 1) == "done"

        assert runner.available_slots == 1
    finally:
        runner.shutdown()


def test_submit_failure_releases_slot(monkeypatch):
    runner = UploadOperationRunner(max_workers=1)
    runner.start()

    def fail_submit(*_args):
        raise RuntimeError("submit failed")

    monkeypatch.setattr(runner._executor, "submit", fail_submit)

    try:
        with pytest.raises(RuntimeError):
            runner.run(lambda _event: None, time.monotonic() + 1)

        assert runner.available_slots == 1
    finally:
        runner.shutdown()


def test_cancelled_future_releases_slot_and_reports_timeout(monkeypatch):
    runner = UploadOperationRunner(max_workers=1)
    runner.start()

    class PendingExecutor:
        def submit(self, *_args):
            return Future()

        def shutdown(self, wait=True, cancel_futures=False):
            return None

    monkeypatch.setattr(runner, "_executor", PendingExecutor())

    try:
        with pytest.raises(UploadDependencyTimeout):
            runner.run(lambda _event: None, time.monotonic() + 0.02)

        assert runner.available_slots == 1
    finally:
        runner.shutdown()


def test_consecutive_operations_share_one_deadline():
    runner = UploadOperationRunner(max_workers=1)
    runner.start()
    deadline = time.monotonic() + 0.15
    second_finished = threading.Event()

    try:
        runner.run(lambda _event: time.sleep(0.09), deadline)

        def second_operation(_event):
            try:
                time.sleep(0.09)
            finally:
                second_finished.set()

        with pytest.raises(UploadDependencyTimeout):
            runner.run(second_operation, deadline)
        assert second_finished.wait(timeout=1)
        assert runner.available_slots == 1
    finally:
        runner.shutdown()


def test_minio_does_not_start_put_after_timeout():
    from app.core.storage import StorageService, UploadCancelled

    bucket_checked = threading.Event()
    continue_bucket_check = threading.Event()
    new_storage_operation_started = threading.Event()

    class FakeMinio:
        def bucket_exists(self, _bucket):
            bucket_checked.set()
            continue_bucket_check.wait(timeout=2)
            return False

        def make_bucket(self, _bucket):
            new_storage_operation_started.set()

        def put_object(self, **_kwargs):
            new_storage_operation_started.set()

    storage = StorageService()
    storage._client = FakeMinio()
    runner = UploadOperationRunner(max_workers=1)
    runner.start()
    upload_cancelled = threading.Event()

    def upload(cancellation_event):
        try:
            return storage.upload_file(
                b"%PDF-1.4",
                "object.pdf",
                cancellation_event=cancellation_event,
            )
        except UploadCancelled:
            upload_cancelled.set()
            raise

    try:
        with pytest.raises(UploadDependencyTimeout):
            runner.run(upload, time.monotonic() + 0.3)

        assert bucket_checked.wait(timeout=1)
        continue_bucket_check.set()
        deadline = time.monotonic() + 1
        while runner.available_slots == 0 and time.monotonic() < deadline:
            time.sleep(0.005)

        assert runner.available_slots == 1
        assert upload_cancelled.is_set()
        assert not new_storage_operation_started.is_set()
    finally:
        continue_bucket_check.set()
        runner.shutdown()


def test_fifth_upload_request_times_out_when_four_slots_are_occupied(client, monkeypatch, tmp_path):
    from app.api.v1.endpoints import documents
    from app.core.upload_timeout import upload_operation_runner

    timeout = 0.2
    monkeypatch.setattr(documents.settings, "UPLOAD_TOTAL_TIMEOUT_SECONDS", timeout)
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    entered = threading.Event()
    release = threading.Event()
    started_count = 0
    started_lock = threading.Lock()

    def occupy_slot(_cancellation_event):
        nonlocal started_count
        with started_lock:
            started_count += 1
            if started_count == 4:
                entered.set()
        release.wait(timeout=2)

    with ThreadPoolExecutor(max_workers=4) as callers:
        occupied = [
            callers.submit(
                upload_operation_runner.run,
                occupy_slot,
                time.monotonic() + 2,
            )
            for _ in range(4)
        ]
        assert entered.wait(timeout=1)

        started = time.monotonic()
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("documento.pdf", b"%PDF-1.4\nconteudo", "application/pdf")},
        )
        elapsed = time.monotonic() - started

        assert response.status_code == 503
        assert elapsed < timeout + 0.5
        assert upload_operation_runner.available_slots == 0

        release.set()
        for future in occupied:
            future.result(timeout=1)

    assert upload_operation_runner.available_slots == 4


def test_slow_minio_returns_503_within_deadline(client, monkeypatch, tmp_path, caplog):
    from app.api.v1.endpoints import documents

    timeout = 0.1
    monkeypatch.setattr(documents.settings, "UPLOAD_TOTAL_TIMEOUT_SECONDS", timeout)
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    entered = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    received_cancellation = []

    class SlowStorage:
        def upload_file(
            self, file_data, object_name, content_type="application/pdf", cancellation_event=None
        ):
            entered.set()
            release.wait(timeout=2)
            received_cancellation.append(cancellation_event.is_set())
            finished.set()
            return f"s3://documents/{object_name}"

    monkeypatch.setattr(documents, "storage_service", SlowStorage())
    started = time.monotonic()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("slow.pdf", b"%PDF-1.4\nconteudo", "application/pdf")},
    )
    elapsed = time.monotonic() - started

    try:
        assert response.status_code == 503
        assert elapsed < timeout + 0.5
        assert entered.wait(timeout=1)
        assert "dependency=minio" in caplog.text
        assert "timeout_seconds=0.100" in caplog.text
    finally:
        release.set()

    assert finished.wait(timeout=1)
    assert received_cancellation == [True]


def test_slow_redis_returns_503_and_marks_document_failed(
    client, db_session, monkeypatch, tmp_path
):
    from app.api.v1.endpoints import documents
    from app.db.models.document import Document

    timeout = 0.75
    monkeypatch.setattr(documents.settings, "UPLOAD_TOTAL_TIMEOUT_SECONDS", timeout)
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    entered = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def slow_delay(*_args, **_kwargs):
        entered.set()
        release.wait(timeout=2)
        finished.set()
        return type("TaskResult", (), {"id": "late-task"})()

    monkeypatch.setattr(documents.process_document_task, "delay", slow_delay)
    started = time.monotonic()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("slow.pdf", b"%PDF-1.4\nconteudo", "application/pdf")},
    )
    elapsed = time.monotonic() - started

    try:
        assert response.status_code == 503
        assert elapsed < timeout + 0.5
        assert entered.wait(timeout=1)
        document = db_session.query(Document).one()
        assert document.status == "EXTRACTION_FAILED"
    finally:
        release.set()

    assert finished.wait(timeout=1)

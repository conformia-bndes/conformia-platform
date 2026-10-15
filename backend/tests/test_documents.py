"""Tests for document upload, validation and retrieval endpoints."""

import io
from types import SimpleNamespace

from app.db.models.document import Document

VALID_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


class _FakeStorage:
    """Substitui o MinIO nos testes de upload."""

    def upload_file(self, file_data, object_name, content_type="application/pdf"):
        return f"s3://documents/{object_name}"


def _patch_storage_ok(monkeypatch):
    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())


def test_upload_invalid_extension(client):
    """Rejeita arquivos que nao possuam extensao .pdf."""
    fake_file = io.BytesIO(b"conteudo de texto simples")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("documento.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_invalid_magic_bytes(client):
    """Rejeita arquivos .pdf sem assinatura binaria %PDF."""
    fake_file = io.BytesIO(b"MALFORMED_HEADER_NOT_A_REAL_PDF")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("documento_falso.pdf", fake_file, "application/pdf")},
    )
    assert response.status_code == 400
    assert "assinatura binaria" in response.json()["detail"]


def test_upload_valid_pdf_file(client, monkeypatch):
    """Aceita arquivo PDF com assinatura valida e processa (modo sincrono explicito)."""
    _patch_storage_ok(monkeypatch)
    fake_file = io.BytesIO(VALID_PDF)

    response = client.post(
        "/api/v1/documents/upload?async_process=false",
        files={"file": ("certidao_teste.pdf", fake_file, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["task_id"] is None
    assert data["filename"] == "certidao_teste.pdf"
    assert data["file_size"] == len(VALID_PDF)


def test_upload_dispatches_task_to_worker_by_default(client, db_session, monkeypatch):
    """O upload padrao despacha a tarefa ao worker e devolve o task_id."""
    _patch_storage_ok(monkeypatch)
    dispatched = {}

    def fake_delay(document_id, file_path, object_name):
        dispatched.update(document_id=document_id, object_name=object_name)
        return SimpleNamespace(id="task-123")

    monkeypatch.setattr("app.api.v1.endpoints.documents.process_document_task.delay", fake_delay)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task_id"] == "task-123"
    assert data["status"] == "PROCESSING"
    assert dispatched["document_id"] == data["id"]
    assert dispatched["object_name"].endswith("_certidao.pdf")

    # O estado do documento tambem e consultavel pela API
    detail = client.get(f"/api/v1/documents/{data['id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "PROCESSING"


def test_upload_returns_503_when_queue_is_down(client, monkeypatch):
    """Broker indisponivel deve virar erro explicito, sem fallback silencioso."""
    _patch_storage_ok(monkeypatch)

    def broken_delay(*args, **kwargs):
        raise ConnectionError("redis fora do ar")

    monkeypatch.setattr("app.api.v1.endpoints.documents.process_document_task.delay", broken_delay)
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
    )
    assert response.status_code == 503
    assert "Fila" in response.json()["detail"]


def test_upload_returns_503_when_storage_is_down(client, monkeypatch):
    """Sem MinIO o worker nao enxerga o arquivo: o upload assincrono deve falhar."""

    class BrokenStorage:
        def upload_file(self, *args, **kwargs):
            raise ConnectionError("minio fora do ar")

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", BrokenStorage())
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
    )
    assert response.status_code == 503


def test_task_status_success(client, monkeypatch):
    """Consulta o estado de uma tarefa concluida e resume o resultado."""
    fake_result = SimpleNamespace(
        state="SUCCESS",
        result={
            "document_id": "doc-1",
            "status": "COMPLETED",
            "compliance_summary": {"overall_status": "MANUAL_REVIEW", "compliance_score": 0.5},
        },
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.AsyncResult", lambda task_id, app=None: fake_result
    )
    response = client.get("/api/v1/documents/tasks/task-123")
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "SUCCESS"
    assert data["result"]["document_id"] == "doc-1"
    assert data["result"]["overall_status"] == "MANUAL_REVIEW"


def test_task_status_failure_exposes_error(client, monkeypatch):
    fake_result = SimpleNamespace(state="FAILURE", result=RuntimeError("boom"))
    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.AsyncResult", lambda task_id, app=None: fake_result
    )
    data = client.get("/api/v1/documents/tasks/task-x").json()
    assert data["state"] == "FAILURE"
    assert "boom" in data["error"]


def test_list_documents(client, db_session):
    """Lista documentos paginados do banco de dados."""
    doc = Document(
        id="doc-list-test-01",
        filename="teste.pdf",
        original_filename="teste.pdf",
        content_type="application/pdf",
        file_size=2048,
        storage_path="/tmp/teste.pdf",
        status="COMPLETED",
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["id"] == "doc-list-test-01" for item in data["items"])


def test_get_document_not_found(client):
    """Retorna 404 para documento inexistente."""
    response = client.get("/api/v1/documents/non-existent-uuid")
    assert response.status_code == 404

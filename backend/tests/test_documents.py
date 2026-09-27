"""Tests for document upload, validation and retrieval endpoints."""

import io
from app.db.models.document import Document


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
    """Aceita arquivo PDF com assinatura valida e processa."""
    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    fake_file = io.BytesIO(valid_pdf_content)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao_teste.pdf", fake_file, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "certidao_teste.pdf"
    assert data["file_size"] == len(valid_pdf_content)


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

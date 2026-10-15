"""Tests for the IDP extractor: native PDFs, scanned PDFs (OCR fallback), errors and contract."""

import io
import shutil

import pytest

from app.idp.extractor import DocumentExtractor
from tests.synthetic_pdfs import SYNTHETIC_LINES, build_native_pdf, build_scanned_pdf

HAS_TESSERACT = shutil.which("tesseract") is not None

TWO_PAGES = [
    ["PAGINA UM - CERTIDAO NEGATIVA DE DEBITOS", "RELATIVOS AOS TRIBUTOS FEDERAIS DA UNIAO"],
    ["PAGINA DOIS - CNPJ: 12.345.678/0001-90", "VALIDA ATE: 31/12/2030 DOCUMENTO SINTETICO"],
]


@pytest.fixture
def native_pdf(tmp_path):
    path = tmp_path / "cnd_nativo.pdf"
    path.write_bytes(build_native_pdf([SYNTHETIC_LINES]))
    return str(path)


@pytest.fixture
def scanned_pdf(tmp_path):
    path = tmp_path / "cnd_digitalizado.pdf"
    path.write_bytes(build_scanned_pdf(SYNTHETIC_LINES))
    return str(path)


def test_native_pdf_returns_text_per_page(native_pdf):
    result = DocumentExtractor().extract(native_pdf, document_id="doc-1")

    assert result["document_id"] == "doc-1"
    assert result["metadata"]["total_pages"] == 1
    page = result["pages"][0]
    assert page["page_number"] == 1
    assert "CERTIDAO NEGATIVA" in page["text"]
    assert page["extraction_method"] == "native"
    assert page["ocr_attempted"] is False
    assert page["error"] is None
    assert result["metadata"]["page_errors"] == []


def test_native_pdf_with_two_pages_separates_text_per_page(tmp_path):
    path = tmp_path / "duas_paginas.pdf"
    path.write_bytes(build_native_pdf(TWO_PAGES))

    result = DocumentExtractor().extract(str(path), document_id="doc-4")

    assert result["metadata"]["total_pages"] == 2
    page1, page2 = result["pages"]
    assert page1["page_number"] == 1
    assert page2["page_number"] == 2
    assert "PAGINA UM" in page1["text"]
    assert "PAGINA DOIS" not in page1["text"]
    assert "PAGINA DOIS" in page2["text"]
    assert "PAGINA UM" not in page2["text"]
    assert result["metadata"]["has_scanned_pages"] is False


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract nao instalado neste ambiente")
def test_scanned_pdf_triggers_ocr_fallback(scanned_pdf):
    result = DocumentExtractor().extract(scanned_pdf, document_id="doc-2")

    page = result["pages"][0]
    assert page["ocr_attempted"] is True
    assert page["extraction_method"] == "ocr"
    assert page["is_scanned"] is True
    assert "CERTIDAO" in page["text"].upper()
    assert result["metadata"]["has_scanned_pages"] is True


def test_ocr_failure_on_all_pages_raises_readable_error(scanned_pdf, monkeypatch):
    monkeypatch.setattr(
        DocumentExtractor,
        "_perform_ocr",
        lambda self, page, page_idx: ("", f"OCR falhou na pagina {page_idx}: Tesseract ausente"),
    )
    with pytest.raises(RuntimeError) as exc:
        DocumentExtractor().extract(scanned_pdf, document_id="doc-3")
    assert "Tesseract ausente" in str(exc.value)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        DocumentExtractor().extract(str(tmp_path / "nao_existe.pdf"))


def test_upload_native_pdf_matches_processing_contract(client):
    """Fluxo completo: upload -> extrator -> parser -> GET /processing (contrato do Pedro)."""
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "cnd_nativo.pdf",
                io.BytesIO(build_native_pdf([SYNTHETIC_LINES])),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    processing = client.get(f"/api/v1/documents/{doc_id}/processing")
    assert processing.status_code == 200
    data = processing.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "COMPLETED"
    assert data["error"] is None
    assert data["extraction"]["document_type"] == "CND_FEDERAL"
    cnpj = data["extraction"]["fields"]["cnpj"]
    assert cnpj["value"] == "12.345.678/0001-90"
    assert cnpj["evidence"]["page"] == 1


def test_upload_scanned_pdf_with_ocr_failure_reports_error(client, monkeypatch):
    """Se o OCR falha em todas as paginas, /processing devolve EXTRACTION_FAILED + erro legivel."""
    monkeypatch.setattr(
        DocumentExtractor,
        "_perform_ocr",
        lambda self, page, page_idx: ("", "OCR falhou na pagina 1: Tesseract ausente"),
    )
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "cnd_digitalizado.pdf",
                io.BytesIO(build_scanned_pdf(SYNTHETIC_LINES)),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    data = client.get(f"/api/v1/documents/{doc_id}/processing").json()
    assert data["document_id"] == doc_id
    assert data["status"] == "EXTRACTION_FAILED"
    assert "Tesseract ausente" in data["error"]["message"]

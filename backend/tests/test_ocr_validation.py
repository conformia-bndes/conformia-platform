"""Testes unitarios para o script de validacao de OCR em container (Issue #46)."""

import io
from pathlib import Path

import pdfplumber
import pytest

from app.idp.extractor import DocumentExtractor
from scripts.validate_ocr_container import (
    SCANNED_CND_LINES,
    build_scanned_pdf,
    validate_ocr,
)


def test_build_scanned_pdf_has_no_native_text_layer():
    """Garante que o PDF sintetico de teste possui apenas imagem rasterizada, forcando OCR."""
    pdf_bytes = build_scanned_pdf(SCANNED_CND_LINES)
    assert pdf_bytes.startswith(b"%PDF-")

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        assert len(pdf.pages) == 1
        native_text = (pdf.pages[0].extract_text() or "").strip()
        assert native_text == ""


def test_validate_ocr_pipeline_extracts_cnd_federal(monkeypatch):
    """Valida que o pipeline IDP aciona fallback OCR no PDF digitalizado e extrai CND_FEDERAL."""
    extractor = DocumentExtractor()

    def _fake_perform_ocr(page, page_num: int):
        return "\n".join(SCANNED_CND_LINES), None

    monkeypatch.setattr(extractor, "_perform_ocr", _fake_perform_ocr)

    summary = validate_ocr(extractor=extractor)
    assert summary["document_id"] == "ocr-container-validation"
    assert summary["extraction_method"] == "ocr"
    assert summary["document_type"] == "CND_FEDERAL"
    assert summary["cnpj"] == "12.345.678/0001-90"
    assert summary["validity_date"] == "2030-12-31"


def test_validate_ocr_raises_when_ocr_fails(monkeypatch):
    """Garante falha explicita quando o binario tesseract retorna erro no container."""
    extractor = DocumentExtractor()

    def _broken_ocr(page, page_num: int):
        return "", "OCR error: tesseract is not installed or it's not in your PATH."

    monkeypatch.setattr(extractor, "_perform_ocr", _broken_ocr)

    with pytest.raises(RuntimeError, match="Nenhuma pagina com texto legivel"):
        validate_ocr(extractor=extractor)


def test_ci_backend_workflow_runs_ocr_validation():
    """Garante que o job build do ci-backend.yml executa validate_ocr_container.py na imagem."""
    repo_root = Path(__file__).resolve().parents[2]
    workflow_content = (repo_root / ".github" / "workflows" / "ci-backend.yml").read_text(
        encoding="utf-8"
    )
    assert "python scripts/validate_ocr_container.py" in workflow_content

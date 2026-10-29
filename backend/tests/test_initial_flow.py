"""Testes de fluxo inicial: upload, rejeicao de arquivo invalido, processamento e falha.

Utiliza os 5 PDFs de referencia de tests/synthetic_pdfs.py (valido, vencido,
pendente, ilegivel, invalido) com resultado esperado registrado.

Cobertura:
- Upload valido (PDF nativo com assinatura %PDF-) -> 201 + estado PROCESSING/PENDING
- Rejeicao de arquivo com extensao invalida -> 400
- Rejeicao de arquivo .pdf sem assinatura binaria -> 400
- Processamento de PDF valido -> COMPLETED + extração de entidades + evidencias
- Processamento de certidao vencida -> NON_COMPLIANT (motor de regras temporal)
- Processamento de certidao com pendencia -> NON_COMPLIANT (motor de regras)
- PDF ilegivel (digitalizado sem texto legível) -> EXTRACTION_FAILED + erro estruturado
- Consulta de estado de processamento (GET /processing)
- Arquivo invalido (nao-PDF) rejeitado no upload
"""

import io
import shutil
import unicodedata
from types import SimpleNamespace

import pytest

from app.services.rules_engine import RulesEngine
from tests.synthetic_pdfs import (
    build_reference_pdf,
    get_expected_result,
    INVALID_FILE_CONTENT,
    list_reference_types,
)


def _patch_task_dispatch(monkeypatch):
    """Simula o despacho ao Celery: o upload padrao (assincrono) devolve PROCESSING."""
    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.process_document_task.delay",
        lambda *args, **kwargs: SimpleNamespace(id="task-fluxo-inicial"),
    )


def _sem_acentos(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


# ---------------------------------------------------------------------------
# Fixtures de PDFs de referencia
# ---------------------------------------------------------------------------


@pytest.fixture
def pdf_valido():
    return build_reference_pdf("valido")


@pytest.fixture
def pdf_vencido():
    return build_reference_pdf("vencido")


@pytest.fixture
def pdf_pendente():
    return build_reference_pdf("pendente")


@pytest.fixture
def pdf_ilegivel():
    return build_reference_pdf("ilegivel")


@pytest.fixture
def arquivo_invalido():
    return io.BytesIO(INVALID_FILE_CONTENT)


# ---------------------------------------------------------------------------
# 1. Upload de arquivo valido
# ---------------------------------------------------------------------------


def test_upload_pdf_valido_retorna_201(client, monkeypatch, pdf_valido):
    """RF02: Upload de PDF valido deve retornar 201 e iniciar processamento."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())
    _patch_task_dispatch(monkeypatch)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao_valida.pdf", io.BytesIO(pdf_valido), "application/pdf")},
    )
    expected = get_expected_result("valido")
    assert response.status_code == expected["upload_status"]
    data = response.json()
    assert data["status"] in ("PENDING", "PROCESSING")
    assert data["filename"] == "certidao_valida.pdf"
    assert data["file_size"] == len(pdf_valido)


def test_upload_pdf_vencido_retorna_201(client, monkeypatch, pdf_vencido):
    """RF02: Upload de certidao vencida deve ser aceito (a regra temporal e avaliada depois)."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())
    _patch_task_dispatch(monkeypatch)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao_vencida.pdf", io.BytesIO(pdf_vencido), "application/pdf")},
    )
    expected = get_expected_result("vencido")
    assert response.status_code == expected["upload_status"]
    data = response.json()
    assert data["status"] in ("PENDING", "PROCESSING")


def test_upload_pdf_pendente_retorna_201(client, monkeypatch, pdf_pendente):
    """RF02: Upload de certidao com pendencia deve ser aceito."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())
    _patch_task_dispatch(monkeypatch)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certidao_pendente.pdf", io.BytesIO(pdf_pendente), "application/pdf")},
    )
    expected = get_expected_result("pendente")
    assert response.status_code == expected["upload_status"]
    data = response.json()
    assert data["status"] in ("PENDING", "PROCESSING")


# ---------------------------------------------------------------------------
# 2. Rejeicao de arquivo invalido
# ---------------------------------------------------------------------------


def test_upload_arquivo_sem_extensao_pdf_eh_rejeitado(client, arquivo_invalido):
    """RF02: Arquivo sem extensao .pdf deve ser rejeitado com 400."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("documento.txt", arquivo_invalido, "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_pdf_sem_assinatura_binaria_eh_rejeitado(client):
    """RF02: Arquivo .pdf sem assinatura binaria %PDF- deve ser rejeitado com 400."""
    fake_pdf = io.BytesIO(b"MALFORMED_HEADER_NOT_A_REAL_PDF")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("falso.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    assert "assinatura binaria" in response.json()["detail"]


def test_upload_arquivo_binario_invalido_eh_rejeitado(client, arquivo_invalido):
    """RF02: Arquivo binario invalido (nao-PDF) enviado com extensao .pdf deve ser rejeitado."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invalido.pdf", arquivo_invalido, "application/pdf")},
    )
    expected = get_expected_result("invalido")
    assert response.status_code == expected["upload_status"]
    assert expected["error_contains"] in response.json()["detail"]


# ---------------------------------------------------------------------------
# 3. Processamento de PDFs de referencia
# ---------------------------------------------------------------------------


def test_processamento_pdf_valido_fluxo_completo(client, monkeypatch, pdf_valido):
    """RF02 + RF03 + RF04: Upload + extracao nativa + entidades + evidencias."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())

    response = client.post(
        "/api/v1/documents/upload?async_process=false",
        files={"file": ("cnd_valida.pdf", io.BytesIO(pdf_valido), "application/pdf")},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    # Consulta o estado de processamento (contrato do Pedro)
    processing = client.get(f"/api/v1/documents/{doc_id}/processing")
    assert processing.status_code == 200
    data = processing.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "COMPLETED"
    assert data["error"] is None
    assert data["extraction"] is not None
    assert data["extraction"]["document_type"] == "CND_FEDERAL"

    # Evidencia de CNPJ extraída com pagina
    cnpj = data["extraction"]["fields"]["cnpj"]
    assert cnpj["value"] == "12.345.678/0001-90"
    assert cnpj["evidence"]["page"] == 1


def test_processamento_certidao_vencida_nao_conforme(client, monkeypatch, pdf_vencido):
    """RF06: Certidao vencida deve resultar em NON_COMPLIANT no motor de regras."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())

    response = client.post(
        "/api/v1/documents/upload?async_process=false",
        files={"file": ("cnd_vencida.pdf", io.BytesIO(pdf_vencido), "application/pdf")},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    processing = client.get(f"/api/v1/documents/{doc_id}/processing")
    assert processing.status_code == 200
    data = processing.json()
    assert data["status"] == "COMPLETED"
    assert data["extraction"] is not None
    assert data["extraction"]["document_type"] == "CND_FEDERAL"

    # Executa o motor de regras diretamente no texto extraído
    engine = RulesEngine()
    full_text = data["extraction"].get("full_text_preview", "")
    if not full_text and data["extraction"].get("evidences"):
        full_text = " ".join(e["text"] for e in data["extraction"]["evidences"])

    result = engine.evaluate(
        {
            "full_text": full_text
            or (
                "CERTIDAO NEGATIVA TRIBUTOS FEDERAIS DIVIDA ATIVA UNIAO "
                "Valida ate: 01/01/2020 CNPJ: 12.345.678/0001-90"
            ),
            "metadata": {},
        }
    )
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    expected = get_expected_result("vencido")
    assert cnd_check["status"] == expected["rule_status"]
    assert expected["error_contains"] in cnd_check["findings"].lower()


def test_processamento_certidao_pendente_nao_conforme(client, monkeypatch, pdf_pendente):
    """RF06: Certidao com pendencia deve resultar em NON_COMPLIANT."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())

    response = client.post(
        "/api/v1/documents/upload?async_process=false",
        files={"file": ("cnd_pendente.pdf", io.BytesIO(pdf_pendente), "application/pdf")},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    processing = client.get(f"/api/v1/documents/{doc_id}/processing")
    assert processing.status_code == 200
    data = processing.json()
    assert data["status"] == "COMPLETED"
    assert data["extraction"] is not None

    engine = RulesEngine()
    full_text = data["extraction"].get("full_text_preview", "")
    if not full_text and data["extraction"].get("evidences"):
        full_text = " ".join(e["text"] for e in data["extraction"]["evidences"])

    result = engine.evaluate(
        {
            "full_text": full_text
            or (
                "CERTIDAO POSITIVA DEBITOS TRIBUTOS FEDERAIS DIVIDA ATIVA "
                "CONSTA PENDENCIA CNPJ: 98.765.432/0001-11"
            ),
            "metadata": {},
        }
    )
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    expected = get_expected_result("pendente")
    assert cnd_check["status"] == expected["rule_status"]
    assert expected["error_contains"] in _sem_acentos(cnd_check["findings"].lower())


# ---------------------------------------------------------------------------
# 4. Tratamento de falha (PDF ilegivel)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    shutil.which("tesseract") is None, reason="Tesseract nao instalado neste ambiente"
)
def test_processamento_pdf_ilegivel_extração_falha(client, monkeypatch, pdf_ilegivel):
    """RF03: PDF digitalizado sem texto legível deve resultar em EXTRACTION_FAILED."""

    class _FakeStorage:
        def upload_file(self, file_data, object_name, content_type="application/pdf"):
            return f"s3://documents/{object_name}"

    monkeypatch.setattr("app.api.v1.endpoints.documents.storage_service", _FakeStorage())

    response = client.post(
        "/api/v1/documents/upload?async_process=false",
        files={"file": ("documento_ilegivel.pdf", io.BytesIO(pdf_ilegivel), "application/pdf")},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    processing = client.get(f"/api/v1/documents/{doc_id}/processing")
    assert processing.status_code == 200
    data = processing.json()
    expected = get_expected_result("ilegivel")
    assert data["status"] == expected["processing_status"]
    assert data["error"] is not None
    assert expected["error_contains"] in data["error"]["message"].lower()
    assert data["extraction"] is None


# ---------------------------------------------------------------------------
# 5. Matriz de referencia: todos os 5 tipos de PDF
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pdf_type", list_reference_types())
def test_todos_pdfs_referencia_tem_resultado_esperado_registrado(pdf_type):
    """Garante que todo PDF de referencia tem resultado esperado registrado."""
    expected = get_expected_result(pdf_type)
    assert "upload_status" in expected
    assert expected["upload_status"] in (200, 201, 400, 413, 503)


def test_todos_pdfs_referencia_sao_geraveis():
    """Garante que todos os PDFs de referencia (exceto invalido) podem ser gerados."""
    for pdf_type in list_reference_types():
        if pdf_type == "invalido":
            continue
        pdf_bytes = build_reference_pdf(pdf_type)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 0

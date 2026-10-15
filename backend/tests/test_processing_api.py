"""Tests for Pydantic v2 schemas and document processing status query API."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.db.models.document import Document
from app.idp.parser import extract_fields_and_evidence
from app.schemas.enums import ProcessingStatus
from app.schemas.error import ErrorDetail, ErrorResponse
from app.schemas.evidence import PageEvidence
from app.schemas.extraction import ExtractedField, ExtractionResult
from app.schemas.processing import ProcessingStatusResponse

# ==============================================================================
# 1. Testes Unitarios dos Schemas Pydantic v2
# ==============================================================================


def test_page_evidence_valid():
    """Valida criacao de PageEvidence com campos obrigatorios text e page."""
    ev = PageEvidence(text="CNPJ: 12.345.678/0001-90", page=1, confidence=0.98)
    assert ev.text == "CNPJ: 12.345.678/0001-90"
    assert ev.page == 1
    assert ev.confidence == 0.98
    assert ev.bounding_box is None


def test_page_evidence_invalid_page():
    """Rejeita PageEvidence com numero de pagina menor que 1."""
    with pytest.raises(ValidationError):
        PageEvidence(text="Texto de teste", page=0)


def test_page_evidence_empty_text():
    """Rejeita PageEvidence com texto vazio."""
    with pytest.raises(ValidationError):
        PageEvidence(text="", page=1)


def test_extracted_field_with_evidence():
    """Valida associacao de PageEvidence a um ExtractedField."""
    ev = PageEvidence(text="Valida ate: 31/12/2026", page=2)
    field = ExtractedField(
        name="data_validade",
        value="2026-12-31",
        raw_value="31/12/2026",
        confidence=1.0,
        evidence=ev,
    )
    assert field.name == "data_validade"
    assert field.value == "2026-12-31"
    assert field.evidence is not None
    assert field.evidence.page == 2
    assert field.evidence.text == "Valida ate: 31/12/2026"


def test_extraction_result_model():
    """Valida construcao completa do modelo ExtractionResult."""
    ev = PageEvidence(text="Inscricao regular", page=1)
    field = ExtractedField(name="situacao", value="REGULAR", evidence=ev)
    result = ExtractionResult(
        document_type="CRF_FGTS",
        fields={"situacao": field},
        evidences=[ev],
        total_pages=1,
        tables=[],
        full_text_preview="Texto do certificado...",
    )
    assert result.document_type == "CRF_FGTS"
    assert "situacao" in result.fields
    assert len(result.evidences) == 1
    assert result.evidences[0].page == 1


def test_error_detail_model():
    """Valida construcao de ErrorDetail e ErrorResponse."""
    err = ErrorDetail(
        code="EXTRACTION_FAILED",
        message="PDF corrompido",
        details={"line": 42},
    )
    assert err.code == "EXTRACTION_FAILED"
    assert err.message == "PDF corrompido"
    assert err.details == {"line": 42}
    assert isinstance(err.timestamp, datetime)

    err_resp = ErrorResponse(error=err)
    assert err_resp.error.code == "EXTRACTION_FAILED"


def test_processing_status_response_validation():
    """Valida ProcessingStatusResponse para estado concluido e em processamento."""
    now = datetime.now(timezone.utc)
    res_completed = ProcessingStatusResponse(
        document_id="doc-uuid-001",
        filename="cnd.pdf",
        status=ProcessingStatus.COMPLETED,
        progress=1.0,
        message="Sucesso",
        extraction=ExtractionResult(total_pages=1),
        error=None,
        created_at=now,
        updated_at=now,
    )
    assert res_completed.status == ProcessingStatus.COMPLETED
    assert res_completed.progress == 1.0

    res_proc = ProcessingStatusResponse(
        document_id="doc-uuid-002",
        filename="crf.pdf",
        status=ProcessingStatus.PROCESSING,
        progress=0.5,
        message="Em processamento",
        extraction=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    assert res_proc.status == ProcessingStatus.PROCESSING
    assert res_proc.progress == 0.5


# ==============================================================================
# 2. Testes de Extracao e Ancoragem de Evidencias no IDP Parser
# ==============================================================================


def test_extract_fields_and_evidence_cnd_federal():
    """Extrai campos e evidencias textuais e de pagina de CND Federal."""
    sample_text = (
        "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
        "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E A DIVIDA ATIVA DA UNIAO\n"
        "CNPJ: 12.345.678/0001-90\n"
        "E certificado que nao constam pendencias em nome do sujeito passivo.\n"
        "Valida ate: 31/12/2026\n"
    )
    pages = [{"page_number": 1, "text": sample_text}]
    result = extract_fields_and_evidence(sample_text, pages=pages)

    assert result.document_type == "CND_FEDERAL"
    assert "cnpj" in result.fields
    assert result.fields["cnpj"].value == "12.345.678/0001-90"
    assert result.fields["cnpj"].evidence.page == 1
    assert "12.345.678/0001-90" in result.fields["cnpj"].evidence.text

    assert "data_validade" in result.fields
    assert result.fields["data_validade"].value == "2026-12-31"
    assert result.fields["data_validade"].evidence.page == 1

    assert "situacao" in result.fields
    assert result.fields["situacao"].value == "REGULAR"

    assert len(result.evidences) >= 3
    for ev in result.evidences:
        assert ev.page >= 1
        assert len(ev.text) > 0


def test_extract_fields_and_evidence_crf_fgts_multipage():
    """Extrai campos ancorados na pagina correta em documento multipagina."""
    page_1 = "CAIXA ECONOMICA FEDERAL\nCERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
    page_2 = (
        "Inscricao: 98.765.432/0001-11\n"
        "A Caixa certifica que a empresa encontra-se em SITUACAO REGULAR.\n"
        "Numero: CRF2026011500123\n"
    )
    full_text = f"{page_1}\n--- [QUEBRA] ---\n{page_2}"
    pages = [
        {"page_number": 1, "text": page_1},
        {"page_number": 2, "text": page_2},
    ]

    result = extract_fields_and_evidence(full_text, pages=pages)

    assert result.document_type == "CRF_FGTS"
    assert result.total_pages == 2
    assert "cnpj" in result.fields
    # CNPJ foi detectado na pagina 2
    assert result.fields["cnpj"].evidence.page == 2
    assert "numero_certidao" in result.fields
    assert result.fields["numero_certidao"].evidence.page == 2


# ==============================================================================
# 3. Testes dos Endpoints de Consulta de Processamento
# ==============================================================================


def test_get_processing_status_completed(client, db_session):
    """Consulta estado de documento concluido com payload de extracao e evidencias."""
    doc = Document(
        id="doc-proc-test-completed",
        filename="cnd_federal.pdf",
        original_filename="cnd_federal.pdf",
        content_type="application/pdf",
        file_size=15420,
        storage_path="/tmp/cnd_federal.pdf",
        status="COMPLETED",
        extracted_text=(
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
            "CNPJ: 11.222.333/0001-44\n"
            "Valida ate: 25/11/2026\n"
            "Nao constam pendencias.\n"
        ),
        extracted_metadata={"total_pages": 1, "has_scanned_pages": False},
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get(f"/api/v1/documents/{doc.id}/processing")
    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == "doc-proc-test-completed"
    assert data["filename"] == "cnd_federal.pdf"
    assert data["status"] == "COMPLETED"
    assert data["progress"] == 1.0
    assert "concluido" in data["message"].lower()

    # Payload de extracao presente
    extraction = data["extraction"]
    assert extraction is not None
    assert extraction["document_type"] == "CND_FEDERAL"
    assert "cnpj" in extraction["fields"]
    assert extraction["fields"]["cnpj"]["value"] == "11.222.333/0001-44"

    # Evidencias com text e page
    evidences = extraction["evidences"]
    assert len(evidences) > 0
    for ev in evidences:
        assert "text" in ev and len(ev["text"]) > 0
        assert "page" in ev and ev["page"] >= 1

    assert data["error"] is None


def test_get_processing_status_in_progress(client, db_session):
    """Consulta documento em processamento (status PROCESSING)."""
    doc = Document(
        id="doc-proc-test-running",
        filename="processando.pdf",
        original_filename="processando.pdf",
        content_type="application/pdf",
        file_size=20000,
        storage_path="/tmp/processando.pdf",
        status="PROCESSING",
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get(f"/api/v1/documents/{doc.id}/processing")
    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == "doc-proc-test-running"
    assert data["status"] == "PROCESSING"
    assert data["progress"] == 0.5
    assert data["extraction"] is None
    assert data["error"] is None


def test_get_processing_status_pending(client, db_session):
    """Consulta documento pendente na fila (status PENDING)."""
    doc = Document(
        id="doc-proc-test-pending",
        filename="pendente.pdf",
        original_filename="pendente.pdf",
        content_type="application/pdf",
        file_size=10000,
        storage_path="/tmp/pendente.pdf",
        status="PENDING",
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get(f"/api/v1/documents/{doc.id}/processing")
    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == "doc-proc-test-pending"
    assert data["status"] == "PENDING"
    assert data["progress"] == 0.0
    assert data["extraction"] is None
    assert data["error"] is None


def test_get_processing_status_failed_with_structured_error(client, db_session):
    """Consulta documento com falha na extracao e detalhes estruturados de erro."""
    doc = Document(
        id="doc-proc-test-failed",
        filename="corrompido.pdf",
        original_filename="corrompido.pdf",
        content_type="application/pdf",
        file_size=500,
        storage_path="/tmp/corrompido.pdf",
        status="EXTRACTION_FAILED",
        extracted_metadata={
            "error_detail": {
                "code": "EXTRACTION_FAILED",
                "message": "Erro ao extrair conteudo: PDF malformado ou corrompido.",
                "details": {"stage": "pdfplumber_parsing", "corrupted": True},
                "timestamp": "2026-10-12T19:00:00Z",
            }
        },
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get(f"/api/v1/documents/{doc.id}/processing")
    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == "doc-proc-test-failed"
    assert data["status"] == "EXTRACTION_FAILED"
    assert data["progress"] == 0.0
    assert data["extraction"] is None

    # Estrutura de erro detalhada
    assert data["error"] is not None
    assert data["error"]["code"] == "EXTRACTION_FAILED"
    assert "PDF malformado" in data["error"]["message"]
    assert data["error"]["details"]["corrupted"] is True


def test_get_processing_status_not_found(client):
    """Retorna 404 para identificador de documento inexistente."""
    response = client.get("/api/v1/documents/non-existent-uuid/processing")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_processing_status_aliases(client, db_session):
    """Verifica que as rotas de alias /status e /extraction respondem equivalentemente."""
    doc = Document(
        id="doc-proc-alias-test",
        filename="teste_alias.pdf",
        original_filename="teste_alias.pdf",
        content_type="application/pdf",
        file_size=1200,
        storage_path="/tmp/teste_alias.pdf",
        status="COMPLETED",
        extracted_text="CNPJ: 00.000.000/0001-00\nSituacao regular.\n",
    )
    db_session.add(doc)
    db_session.commit()

    resp_proc = client.get(f"/api/v1/documents/{doc.id}/processing")
    resp_stat = client.get(f"/api/v1/documents/{doc.id}/status")
    resp_extr = client.get(f"/api/v1/documents/{doc.id}/extraction")

    assert resp_proc.status_code == 200
    assert resp_stat.status_code == 200
    assert resp_extr.status_code == 200
    assert resp_proc.json()["status"] == resp_stat.json()["status"]
    assert resp_proc.json()["status"] == resp_extr.json()["status"]

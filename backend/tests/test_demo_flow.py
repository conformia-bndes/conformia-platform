"""Testes automatizados do roteiro de demonstracao do MVP (Issue #63)."""

from datetime import date
from pathlib import Path

import pdfplumber
import pytest

from app.api.v1.endpoints import documents
from app.core.config import ApiUser, settings
from app.core.security import hash_api_key
from app.idp.extractor import DocumentExtractor
from app.idp.parser import extract_fields_and_evidence
from app.services.rules_engine import RulesEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"
DEMO_REF_DATE = date(2026, 11, 22)

DEMO_KEYS = {
    "analista.maker": "analista.maker:segredo-demo-maker",
    "analista.checker": "analista.checker:segredo-demo-checker",
}
DEMO_HASHES = {uid: hash_api_key(raw.split(":", 1)[1]) for uid, raw in DEMO_KEYS.items()}


@pytest.fixture(autouse=True)
def _demo_environment(monkeypatch, tmp_path):
    """Isola UPLOAD_DIR, data de referencia e usuarios de demonstracao."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(
        settings,
        "API_USERS",
        [
            ApiUser(
                user_id="analista.maker",
                role="ANALISTA",
                key_hash=DEMO_HASHES["analista.maker"],
            ),
            ApiUser(
                user_id="analista.checker",
                role="ANALISTA",
                key_hash=DEMO_HASHES["analista.checker"],
            ),
        ],
    )
    monkeypatch.setattr(
        "app.services.compliance_service.RulesEngine",
        lambda *args, **kwargs: RulesEngine(*args, **{**kwargs, "today": lambda: DEMO_REF_DATE}),
    )


def _upload_and_verify(client, filename: str):
    pdf_path = SAMPLES_DIR / filename
    assert pdf_path.is_file(), f"Arquivo de demo ausente: {pdf_path}"
    content = pdf_path.read_bytes()
    assert content.startswith(b"%PDF-")

    upload_resp = client.post(
        "/api/v1/documents/upload?async_process=false",
        files={"file": (filename, content, "application/pdf")},
    )
    assert upload_resp.status_code == 201, upload_resp.text
    upload_data = upload_resp.json()
    assert upload_data["status"] == "COMPLETED"

    verify_resp = client.post(f"/api/v1/compliance/verify/{upload_data['id']}")
    assert verify_resp.status_code == 200, verify_resp.text
    return upload_data["id"], verify_resp.json()


def test_demo_samples_inventory_exists():
    """Garante presenca de todos os PDFs ficticios descritos no roteiro de demo."""
    expected = {
        "cnd_federal_ficticia_apresentacao.pdf",
        "cnd_federal_vencida.pdf",
        "cnd_federal_sem_validade.pdf",
        "cnd_federal_positiva_reprovada.pdf",
        "crf_fgts_conforme.pdf",
        "cndt_trabalhista_reprovada.pdf",
        "licenca_ambiental_revisao_manual.pdf",
        "cnd_federal_digitalizada_ocr.pdf",
    }
    present = {p.name for p in SAMPLES_DIR.glob("*.pdf")}
    assert expected <= present


def test_demo_core_script_cnd_scenarios_human_review_and_audit(client):
    """Executa os 5 atos do roteiro: CND valida, vencida, sem validade, 4 olhos e auditoria."""
    # Ato 1: CND valida -> COMPLIANT
    _, valid_report = _upload_and_verify(client, "cnd_federal_ficticia_apresentacao.pdf")
    assert valid_report["document_type"] == "CND_FEDERAL"
    assert valid_report["overall_status"] == "COMPLIANT"
    valid_rule = next(c for c in valid_report["checks"] if c["rule_id"] == "RULE-BNDES-001")
    assert valid_rule["status"] == "COMPLIANT"

    # Ato 2: CND vencida -> NON_COMPLIANT
    _, expired_report = _upload_and_verify(client, "cnd_federal_vencida.pdf")
    assert expired_report["document_type"] == "CND_FEDERAL"
    assert expired_report["overall_status"] == "NON_COMPLIANT"
    expired_rule = next(c for c in expired_report["checks"] if c["rule_id"] == "RULE-BNDES-001")
    assert expired_rule["status"] == "NON_COMPLIANT"

    # Ato 3: CND sem data de validade -> MANUAL_REVIEW_REQUIRED
    manual_doc_id, manual_report = _upload_and_verify(client, "cnd_federal_sem_validade.pdf")
    assert manual_report["document_type"] == "CND_FEDERAL"
    assert manual_report["overall_status"] == "MANUAL_REVIEW_REQUIRED"
    manual_rule = next(c for c in manual_report["checks"] if c["rule_id"] == "RULE-BNDES-001")
    assert manual_rule["status"] == "MANUAL_REVIEW_REQUIRED"
    assert "Data de validade da certidao nao identificada" in manual_rule["findings"]

    # Ato 4: Decisao humana segregada (Maker -> bloqueio 403 -> Checker)
    propose_resp = client.post(
        f"/api/v1/compliance/reviews/{manual_doc_id}",
        json={
            "decision": "APPROVE",
            "justification": (
                "Conferencia manual realizada na demo com comprovante original valido."
            ),
        },
        headers={"X-API-Key": DEMO_KEYS["analista.maker"]},
    )
    assert propose_resp.status_code == 201, propose_resp.text
    proposal_id = propose_resp.json()["id"]

    self_confirm = client.post(
        f"/api/v1/compliance/reviews/{manual_doc_id}/{proposal_id}/confirm",
        json={"comment": "Tentativa de autoconfirmacao deve falhar."},
        headers={"X-API-Key": DEMO_KEYS["analista.maker"]},
    )
    assert self_confirm.status_code == 403

    confirm_resp = client.post(
        f"/api/v1/compliance/reviews/{manual_doc_id}/{proposal_id}/confirm",
        json={"comment": "Segundo analista confirma parecer apos conferencia documental."},
        headers={"X-API-Key": DEMO_KEYS["analista.checker"]},
    )
    assert confirm_resp.status_code == 201, confirm_resp.text

    review_state = client.get(f"/api/v1/compliance/reviews/{manual_doc_id}").json()
    assert review_state["state"] == "FINAL"
    assert review_state["final_decision"] == "APPROVE"

    # Ato 5: Trilha de auditoria imutavel
    audit_resp = client.get("/api/v1/compliance/audit-trail?limit=100")
    assert audit_resp.status_code == 200
    doc_actions = [
        item["action"] for item in audit_resp.json()["items"] if item["entity_id"] == manual_doc_id
    ]
    assert "DOCUMENT_UPLOADED" in doc_actions
    assert "COMPLIANCE_EVALUATION" in doc_actions
    assert "REVIEW_PROPOSED" in doc_actions
    assert "REVIEW_CONFIRMED" in doc_actions


@pytest.mark.parametrize(
    ("filename", "expected_type", "expected_status"),
    [
        ("cnd_federal_positiva_reprovada.pdf", "CND_FEDERAL", "NON_COMPLIANT"),
        ("crf_fgts_conforme.pdf", "CRF_FGTS", "COMPLIANT"),
        ("cndt_trabalhista_reprovada.pdf", "CNDT_TRABALHISTA", "NON_COMPLIANT"),
    ],
)
def test_demo_additional_sample_pdfs_match_expected_outcomes(
    client, filename, expected_type, expected_status
):
    """Valida os demais PDFs ficticios de demonstracao contra o motor."""
    _, report = _upload_and_verify(client, filename)
    assert report["document_type"] == expected_type
    assert report["overall_status"] == expected_status


def test_demo_scanned_pdf_ocr_and_native_plan_b(monkeypatch):
    """Confirma que o PDF digitalizado exige OCR e que o Plano B nativo funciona sem OCR."""
    scanned_path = SAMPLES_DIR / "cnd_federal_digitalizada_ocr.pdf"
    with pdfplumber.open(scanned_path) as pdf:
        assert len(pdf.pages) == 1
        assert (pdf.pages[0].extract_text() or "").strip() == ""

    extractor = DocumentExtractor()
    monkeypatch.setattr(
        extractor,
        "_perform_ocr",
        lambda _page, _num: (
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 15/05/2027",
            None,
        ),
    )
    ocr_result = extractor.extract(str(scanned_path), document_id="demo-ocr")
    assert ocr_result["pages"][0]["extraction_method"] == "ocr"
    parsed = extract_fields_and_evidence(ocr_result["full_text"], pages=ocr_result["pages"])
    assert parsed.document_type == "CND_FEDERAL"

    # Plano B: PDF nativo conclui sem acionar _perform_ocr.
    native_extractor = DocumentExtractor()
    monkeypatch.setattr(
        native_extractor,
        "_perform_ocr",
        lambda *_args, **_kwargs: pytest.fail("Plano B nativo nao pode depender de OCR"),
    )
    native_result = native_extractor.extract(
        str(SAMPLES_DIR / "cnd_federal_ficticia_apresentacao.pdf"),
        document_id="demo-plan-b",
    )
    assert native_result["pages"][0]["extraction_method"] == "native"

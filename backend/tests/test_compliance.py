"""Tests for compliance rules engine and endpoints."""

from app.services.rules_engine import RulesEngine
from app.db.models.compliance import AuditLog, ComplianceCheck
from app.db.models.document import Document


def test_rules_engine_deterministic_compliant():
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "Constatada a nao existencia de pendencias para o CNPJ 00.000.000/0001-91.\n"
            "Valida ate: 31/12/2099"
        ),
        "metadata": {"total_pages": 1},
    }
    result = engine.evaluate(mock_data)
    assert result["total_rules"] >= 1
    # RULE-BNDES-001 (CND) deve ser COMPLIANT
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "COMPLIANT"


def test_rules_engine_anti_keyword_violation():
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "MINISTÉRIO DA FAZENDA\n"
            "CERTIDÃO POSITIVA - CONSTA PENDÊNCIA RELATIVA AOS TRIBUTOS FEDERAIS"
        ),
        "metadata": {"total_pages": 1},
    }
    result = engine.evaluate(mock_data)
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "NON_COMPLIANT"


def test_api_compliance_rules_catalog(client):
    response = client.get("/api/v1/compliance/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert len(data["rules"]) > 0


def test_api_verify_document_compliance_flow(client, db_session):
    # Insere documento no banco
    doc = Document(
        id="test-doc-uuid-123",
        filename="cnd_federal.pdf",
        original_filename="cnd_federal.pdf",
        content_type="application/pdf",
        file_size=1024,
        storage_path="/tmp/cnd.pdf",
        status="COMPLETED",
        extracted_text=(
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO. "
            "CERTIFICADO DE REGULARIDADE DO FGTS REGULAR. "
            "FALENCIA RECUPERACAO JUDICIAL NADA CONSTA."
        ),
    )
    db_session.add(doc)
    db_session.commit()

    response = client.post(f"/api/v1/compliance/verify/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == doc.id
    assert "overall_status" in data
    assert len(data["checks"]) > 0

    # Verifica trilha de auditoria
    audit_resp = client.get("/api/v1/compliance/audit-trail")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["total"] >= 1


VALID_CND_TEXT = (
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E A DIVIDA ATIVA DA UNIAO\n"
    "CNPJ: 12.345.678/0001-90\n"
    "Valida ate: 31/12/2099"
)


def _add_document(db_session, text, doc_id="doc-service-1"):
    doc = Document(
        id=doc_id,
        filename=f"{doc_id}.pdf",
        original_filename=f"{doc_id}.pdf",
        content_type="application/pdf",
        file_size=10,
        storage_path=f"/tmp/{doc_id}.pdf",
        status="COMPLETED",
        extracted_text=text,
    )
    db_session.add(doc)
    db_session.commit()
    return doc


def test_verify_valid_cnd_is_compliant_and_scoped_to_its_type(client, db_session):
    """Fatia vertical: CND valida -> COMPLIANT, sem reprovacao por regras de outros tipos."""
    doc = _add_document(db_session, VALID_CND_TEXT)

    data = client.post(f"/api/v1/compliance/verify/{doc.id}").json()

    assert data["document_type"] == "CND_FEDERAL"
    assert data["overall_status"] == "COMPLIANT"
    assert data["evaluated_rules"] == 1
    statuses = {c["rule_id"]: c["status"] for c in data["checks"]}
    assert statuses["RULE-BNDES-001"] == "COMPLIANT"
    assert {s for rid, s in statuses.items() if rid != "RULE-BNDES-001"} == {"NOT_APPLICABLE"}


def test_verify_unidentified_document_requires_manual_review(client, db_session):
    doc = _add_document(db_session, "Texto qualquer sem tipologia reconhecivel.")

    data = client.post(f"/api/v1/compliance/verify/{doc.id}").json()

    assert data["document_type"] is None
    assert data["overall_status"] == "MANUAL_REVIEW_REQUIRED"
    assert data["evaluated_rules"] == 0


def test_verify_is_idempotent_and_audited_each_time(client, db_session):
    doc = _add_document(db_session, VALID_CND_TEXT)

    client.post(f"/api/v1/compliance/verify/{doc.id}")
    client.post(f"/api/v1/compliance/verify/{doc.id}")

    checks = db_session.query(ComplianceCheck).filter_by(document_id=doc.id).count()
    assert checks == len(RulesEngine().rules)
    audits = db_session.query(AuditLog).filter_by(entity_id=doc.id, action="COMPLIANCE_EVALUATION")
    assert audits.count() == 2
    assert audits.first().details["document_type"] == "CND_FEDERAL"


def test_results_score_excludes_not_applicable_rules(client, db_session):
    doc = _add_document(db_session, VALID_CND_TEXT)
    client.post(f"/api/v1/compliance/verify/{doc.id}")

    data = client.get(f"/api/v1/compliance/results/{doc.id}").json()

    assert data["overall_status"] == "COMPLIANT"
    assert data["compliance_score"] == 1.0
    assert data["evaluated_rules"] == 1


def test_worker_task_extracts_evaluates_and_completes(db_session, monkeypatch, tmp_path):
    """Executa a tarefa Celery de ponta a ponta (sem broker) com um PDF nativo sintetico."""
    from app.core.celery_app import process_document_task
    from tests.conftest import TestingSessionLocal
    from tests.synthetic_pdfs import build_native_pdf

    pdf_path = tmp_path / "cnd.pdf"
    pdf_path.write_bytes(build_native_pdf([VALID_CND_TEXT.splitlines()]))
    doc = _add_document(db_session, None, doc_id="doc-worker-1")
    doc.status = "PROCESSING"
    db_session.commit()
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSessionLocal)

    result = process_document_task(doc.id, str(pdf_path))

    assert result["status"] == "COMPLETED"
    assert result["compliance_summary"]["overall_status"] == "COMPLIANT"
    db_session.expire_all()
    stored = db_session.get(Document, doc.id)
    assert stored.status == "COMPLETED"
    assert stored.extracted_metadata["extraction"]["document_type"] == "CND_FEDERAL"
    assert db_session.query(AuditLog).filter_by(performed_by="CELERY_WORKER").count() == 1

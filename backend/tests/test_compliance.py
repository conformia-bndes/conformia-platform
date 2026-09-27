"""Tests for compliance rules engine and endpoints."""

from app.services.rules_engine import RulesEngine
from app.db.models.document import Document


def test_rules_engine_deterministic_compliant():
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPÚBLICA FEDERATIVA DO BRASIL - MINISTÉRIO DA FAZENDA\n"
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO\n"
            "Constatada a não existência de pendências para o CNPJ 00.000.000/0001-91."
        ),
        "metadata": {"total_pages": 1}
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
        "metadata": {"total_pages": 1}
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
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO. "
            "CERTIFICADO DE REGULARIDADE DO FGTS REGULAR. "
            "FALÊNCIA RECUPERAÇÃO JUDICIAL NADA CONSTA."
        )
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

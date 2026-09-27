"""Advanced unit tests for rules engine: regex validation and temporal validity."""

from app.services.rules_engine import RulesEngine


def test_rules_engine_expired_certificate():
    """Certidao com data de validade expirada deve ser NON_COMPLIANT."""
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 01/01/2020"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data)
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "NON_COMPLIANT"
    assert "expirada" in cnd_check["findings"].lower()


def test_rules_engine_valid_future_certificate():
    """Certidao com data futura valida deve ser COMPLIANT."""
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 31/12/2030"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data)
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "COMPLIANT"


def test_rules_engine_category_filtering():
    """Ao filtrar por categoria FISCAL, regras TRABALHISTA devem ser NOT_APPLICABLE."""
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data, target_category="FISCAL")
    fiscal_check = next(r for r in result["results"] if r["category"] == "FISCAL")
    other_checks = [r for r in result["results"] if r["category"] != "FISCAL"]

    assert fiscal_check["status"] == "COMPLIANT"
    assert all(r["status"] == "NOT_APPLICABLE" for r in other_checks)

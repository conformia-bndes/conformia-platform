"""Advanced unit tests for rules engine: regex validation and temporal validity."""

from datetime import date

from app.services.rules_engine import RulesEngine, summarize_statuses


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
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 31/12/2099"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data, target_category="FISCAL")
    fiscal_check = next(r for r in result["results"] if r["category"] == "FISCAL")
    other_checks = [r for r in result["results"] if r["category"] != "FISCAL"]

    assert fiscal_check["status"] == "COMPLIANT"
    assert all(r["status"] == "NOT_APPLICABLE" for r in other_checks)


CND_TEXT = (
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
    "E A DIVIDA ATIVA DA UNIAO\n"
    "CNPJ: 12.345.678/0001-90\n"
)
FIXED_TODAY = date(2026, 10, 29)


def _cnd_status(text: str) -> str:
    engine = RulesEngine(today=lambda: FIXED_TODAY)
    result = engine.evaluate({"full_text": text}, document_type="CND_FEDERAL")
    return next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")["status"]


def test_missing_validity_date_requires_manual_review():
    """AGENTS.md diretriz 1: sem data de validade legivel, nunca COMPLIANT."""
    assert _cnd_status(CND_TEXT) == "MANUAL_REVIEW_REQUIRED"


def test_validity_on_reference_day_is_still_valid():
    """A certidao vale ate o fim do dia de validade."""
    assert _cnd_status(CND_TEXT + "Valida ate: 29/10/2026") == "COMPLIANT"


def test_validity_one_day_before_reference_is_expired():
    assert _cnd_status(CND_TEXT + "Valida ate: 28/10/2026") == "NON_COMPLIANT"


def test_unparseable_validity_date_requires_manual_review():
    """Data impossivel (31/02) nao e tratada como validade."""
    assert _cnd_status(CND_TEXT + "Valida ate: 31/02/2027") == "MANUAL_REVIEW_REQUIRED"


def test_document_type_scopes_rules_to_matching_code():
    """Uma CND valida nao pode ser reprovada pelas regras de CRF, CNDT, falencia etc."""
    engine = RulesEngine(today=lambda: FIXED_TODAY)
    result = engine.evaluate(
        {"full_text": CND_TEXT + "Valida ate: 31/12/2026"}, document_type="CND_FEDERAL"
    )
    by_rule = {r["rule_id"]: r["status"] for r in result["results"]}

    assert by_rule["RULE-BNDES-001"] == "COMPLIANT"
    assert all(
        status == "NOT_APPLICABLE" for rid, status in by_rule.items() if rid != "RULE-BNDES-001"
    )
    assert result["overall_status"] == "COMPLIANT"
    assert result["evaluated_rules"] == 1
    assert result["compliance_score"] == 1.0


def test_document_type_without_matching_rule_is_manual_review():
    engine = RulesEngine(today=lambda: FIXED_TODAY)
    result = engine.evaluate({"full_text": CND_TEXT}, document_type="TIPO_SEM_REGRA")
    assert result["evaluated_rules"] == 0
    assert result["overall_status"] == "MANUAL_REVIEW_REQUIRED"


def test_not_evaluable_is_manual_review_and_applies_no_rule():
    engine = RulesEngine()
    result = engine.not_evaluable("Tipologia nao identificada.")
    assert result["overall_status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["compliance_score"] == 0.0
    assert all(r["status"] == "NOT_APPLICABLE" for r in result["results"])


def test_summarize_statuses_ignores_not_applicable():
    assert summarize_statuses(["COMPLIANT", "NOT_APPLICABLE"]) == ("COMPLIANT", 1.0)
    assert summarize_statuses(["COMPLIANT", "MANUAL_REVIEW_REQUIRED"]) == (
        "MANUAL_REVIEW_REQUIRED",
        0.5,
    )
    assert summarize_statuses(["COMPLIANT", "NON_COMPLIANT", "MANUAL_REVIEW_REQUIRED"])[0] == (
        "NON_COMPLIANT"
    )
    assert summarize_statuses(["NOT_APPLICABLE"]) == ("MANUAL_REVIEW_REQUIRED", 0.0)
    assert summarize_statuses([]) == ("MANUAL_REVIEW_REQUIRED", 0.0)

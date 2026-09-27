"""Unit tests for Maker-Checker LLM validation."""

from app.ai.llm_client import MakerCheckerValidator


def test_maker_checker_fallback():
    """Valida que o Maker-Checker executa fallback controlado sem chaves de API externas."""
    validator = MakerCheckerValidator()
    rule = {
        "id": "RULE-BNDES-003",
        "title": "Certidao Negativa de Falencia",
        "required_keywords": ["FALENCIA", "NADA CONSTA"],
    }
    sample_text = "TRIBUNAL DE JUSTICA - CERTIDAO DE FALENCIA - NADA CONSTA A RESPEITO DO REU."
    result = validator.evaluate_rule(rule, sample_text)

    assert "status" in result
    assert "final_confidence" in result
    assert result["status"] in ("COMPLIANT", "MANUAL_REVIEW_REQUIRED")

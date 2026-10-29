"""Unit tests for Maker-Checker LLM validation (fail-closed behaviour)."""

import json

import httpx
import pytest

from app.ai.llm_client import (
    LLMClient,
    LLMUnavailableError,
    MakerCheckerValidator,
    is_grounded_in_document,
)

RULE = {
    "id": "RULE-BNDES-004",
    "title": "Certidao Negativa de Falencia",
    "required_keywords": ["FALENCIA", "NADA CONSTA"],
}
DOCUMENT = "TRIBUNAL DE JUSTICA - CERTIDAO DE FALENCIA - NADA CONSTA A RESPEITO DO REU."


class _ScriptedClient:
    """Cliente LLM falso: devolve as respostas em ordem (Maker, depois Checker)."""

    def __init__(self, *responses):
        self._responses = list(responses)

    def generate(self, prompt, system_prompt=None):
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _maker(assessment="COMPLIANT", citation="NADA CONSTA A RESPEITO DO REU", confidence=0.9):
    return json.dumps(
        {
            "assessment": assessment,
            "extracted_value": citation,
            "confidence": confidence,
            "reasoning": "Trecho literal confirma ausencia de falencia.",
        }
    )


def _checker(validation="APPROVED", hallucination=False, confidence=0.95):
    payload = {"validation": validation, "critique": "ok", "confidence": confidence}
    if hallucination is not None:
        payload["hallucination_detected"] = hallucination
    return json.dumps(payload)


def _run(*responses):
    return MakerCheckerValidator(client=_ScriptedClient(*responses)).evaluate_rule(RULE, DOCUMENT)


def test_without_api_key_degrades_to_manual_review_without_fabricated_output(monkeypatch):
    """Sem chave de LLM nao ha resposta simulada: revisao manual e nenhuma evidencia inventada."""
    monkeypatch.setattr("app.ai.llm_client.settings.OPENAI_API_KEY", None)
    result = MakerCheckerValidator().evaluate_rule(RULE, DOCUMENT)

    assert result["status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["error"] == "LLM_UNAVAILABLE"
    assert result["maker_output"] is None
    assert result["checker_output"] is None
    assert result["is_verified"] is False
    assert result["final_confidence"] == 0.0


def test_provider_failure_raises_llm_unavailable(monkeypatch):
    def failing_post(*args, **kwargs):
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(httpx, "post", failing_post)
    with pytest.raises(LLMUnavailableError):
        LLMClient(api_key="test-key").generate("prompt")


def test_grounded_and_approved_proposal_is_accepted():
    result = _run(_maker(), _checker())
    assert result["status"] == "COMPLIANT"
    assert result["is_verified"] is True
    assert result["evidence_grounded"] is True


def test_citation_absent_from_document_degrades_to_manual_review():
    """Checker aprovou, mas a citacao do Maker nao existe no documento (alucinacao)."""
    result = _run(_maker(citation="Certidao valida ate 31/12/2026"), _checker())
    assert result["status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["evidence_grounded"] is False


def test_checker_rejection_degrades_to_manual_review():
    assert _run(_maker(), _checker(validation="REJECTED"))["status"] == "MANUAL_REVIEW_REQUIRED"


def test_checker_must_explicitly_deny_hallucination():
    assert _run(_maker(), _checker(hallucination=None))["status"] == "MANUAL_REVIEW_REQUIRED"
    assert _run(_maker(), _checker(hallucination=True))["status"] == "MANUAL_REVIEW_REQUIRED"


def test_assessment_outside_domain_degrades_to_manual_review():
    assert _run(_maker(assessment="APROVADO"), _checker())["status"] == "MANUAL_REVIEW_REQUIRED"


@pytest.mark.parametrize("maker_raw", ["nao e json", "[1, 2]", ""])
def test_malformed_maker_response_degrades_to_manual_review(maker_raw):
    assert _run(maker_raw, _checker())["status"] == "MANUAL_REVIEW_REQUIRED"


def test_malformed_checker_response_degrades_to_manual_review():
    assert _run(_maker(), "{quebrado")["status"] == "MANUAL_REVIEW_REQUIRED"


def test_non_numeric_confidence_does_not_break_evaluation():
    result = _run(_maker(confidence="alta"), _checker())
    assert result["status"] == "COMPLIANT"
    assert 0.0 <= result["final_confidence"] <= 1.0


def test_is_grounded_ignores_accents_case_and_spacing():
    assert is_grounded_in_document("nada   consta", "CERTIDÃO: NADA CONSTA")
    assert not is_grounded_in_document("", DOCUMENT)
    assert not is_grounded_in_document(None, DOCUMENT)
    assert not is_grounded_in_document("CONSTA DEBITO", DOCUMENT)

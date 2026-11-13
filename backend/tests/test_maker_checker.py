"""Unit tests for Maker-Checker LLM validation (fail-closed behaviour)."""

import json

import httpx
import pytest

from app.ai.llm_client import (
    LLMClient,
    LLMUnavailableError,
    MakerCheckerValidator,
    _parse_json_object,
    is_grounded_in_document,
)
from app.core.config import settings

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


def test_generate_uses_configured_base_url(monkeypatch):
    """LLM_BASE_URL permite apontar para um provedor compativel com OpenAI (ex.: Ollama)."""
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        return _ok_response()

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(settings, "LLM_BASE_URL", "http://ollama.local:11434/v1/")
    assert LLMClient(api_key="test-key").generate("prompt") == "ok"
    assert captured["url"] == "http://ollama.local:11434/v1/chat/completions"


def test_generate_defaults_to_openai_base_url(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        return _ok_response()

    monkeypatch.setattr(httpx, "post", fake_post)
    LLMClient(api_key="test-key").generate("prompt")
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"


def _ok_response(content="ok"):
    request = httpx.Request("POST", "http://llm.test/chat/completions")
    return httpx.Response(
        200, json={"choices": [{"message": {"content": content}}]}, request=request
    )


def _status_response(status):
    request = httpx.Request("POST", "http://llm.test/chat/completions")
    return httpx.Response(status, json={"error": {"message": "erro"}}, request=request)


def test_generate_requests_json_object_and_uses_configured_timeout(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return _ok_response()

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(settings, "LLM_TIMEOUT_SECONDS", 45.0)
    LLMClient(api_key="test-key").generate("prompt")
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert captured["timeout"] == 45.0


def test_generate_retries_on_rate_limit_and_then_succeeds(monkeypatch):
    responses = [_status_response(429), _status_response(503), _ok_response("pronto")]
    sleeps = []
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: responses.pop(0))
    monkeypatch.setattr("app.ai.llm_client.time.sleep", sleeps.append)
    monkeypatch.setattr(settings, "LLM_MAX_RETRIES", 2)
    assert LLMClient(api_key="test-key").generate("prompt") == "pronto"
    assert sleeps == [2.0, 4.0]


def test_generate_gives_up_after_max_retries(monkeypatch):
    calls = []

    def always_429(*args, **kwargs):
        calls.append(1)
        return _status_response(429)

    monkeypatch.setattr(httpx, "post", always_429)
    monkeypatch.setattr("app.ai.llm_client.time.sleep", lambda _: None)
    monkeypatch.setattr(settings, "LLM_MAX_RETRIES", 2)
    with pytest.raises(LLMUnavailableError):
        LLMClient(api_key="test-key").generate("prompt")
    assert len(calls) == 3


def test_generate_does_not_retry_client_errors(monkeypatch):
    calls = []

    def unauthorized(*args, **kwargs):
        calls.append(1)
        return _status_response(401)

    monkeypatch.setattr(httpx, "post", unauthorized)
    monkeypatch.setattr("app.ai.llm_client.time.sleep", lambda _: pytest.fail("nao deve esperar"))
    with pytest.raises(LLMUnavailableError):
        LLMClient(api_key="test-key").generate("prompt")
    assert len(calls) == 1


def test_parse_json_object_accepts_markdown_code_fence():
    fenced = '```json\n{"assessment": "COMPLIANT"}\n```'
    assert _parse_json_object(fenced) == {"assessment": "COMPLIANT"}
    assert _parse_json_object('```\n{"a": 1}\n```') == {"a": 1}
    assert _parse_json_object("nao e json") is None
    assert _parse_json_object("[1, 2]") is None


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

"""RULE-BNDES-005 e 006 pelo motor de regras com o Maker-Checker real e um LLM falso.

O cliente de LLM e injetado em MakerCheckerValidator(client=...): sem rede e sem .env.
Assim a sintese real (aprovacao do Checker + citacao existente no documento) e exercida.
"""

import json
from datetime import date

import pytest

from app.ai.llm_client import LLMUnavailableError, MakerCheckerValidator
from app.services.rules_engine import RulesEngine

FIXED_TODAY = date(2026, 10, 29)

_CEIS = "CADASTRO NACIONAL DE EMPRESAS INIDÔNEAS E SUSPENSAS (CEIS)"
_CNEP = "CADASTRO NACIONAL DE EMPRESAS PUNIDAS (CNEP)"

LICENCA_TEXT = (
    "SECRETARIA ESTADUAL DO MEIO AMBIENTE\n"
    "LICENÇA AMBIENTAL DE OPERAÇÃO Nº 123/2025\n"
    "ÓRGÃO AMBIENTAL: SEMA\n"
    "VÁLIDA ATÉ: 31/12/2027\n"
)
CEIS_CNEP_TEXT = (
    "PORTAL DA TRANSPARÊNCIA - CONSULTA DE SANÇÕES\n"
    f"{_CEIS}\nNADA CONSTA\n"
    f"{_CNEP}\nNADA CONSTA\n"
)

# (rule_id, document_type, texto conforme, citacao literal presente, termo de bloqueio)
RULES = [
    pytest.param(
        "RULE-BNDES-005",
        "LICENCA_AMBIENTAL",
        LICENCA_TEXT,
        "LICENÇA AMBIENTAL DE OPERAÇÃO Nº 123/2025",
        "EMBARGADO",
        id="005",
    ),
    pytest.param(
        "RULE-BNDES-006",
        "INTEGRIDADE_CEIS_CNEP",
        CEIS_CNEP_TEXT,
        "NADA CONSTA",
        "IMPEDIMENTO DE LICITAR",
        id="006",
    ),
]


class _ScriptedClient:
    """Cliente LLM falso: devolve as respostas em ordem (Maker, depois Checker)."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = 0

    def generate(self, prompt, system_prompt=None):
        self.calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _maker(citation, assessment="COMPLIANT"):
    return json.dumps(
        {
            "assessment": assessment,
            "extracted_value": citation,
            "confidence": 0.9,
            "reasoning": "Trecho literal fundamenta a avaliacao.",
        }
    )


def _checker(validation="APPROVED"):
    return json.dumps(
        {
            "validation": validation,
            "critique": "ok",
            "hallucination_detected": False,
            "confidence": 0.95,
        }
    )


def _evaluate(rule_id, document_type, text, client):
    engine = RulesEngine(
        maker_checker=MakerCheckerValidator(client=client), today=lambda: FIXED_TODAY
    )
    result = engine.evaluate({"full_text": text, "metadata": {}}, document_type=document_type)
    return next(r for r in result["results"] if r["rule_id"] == rule_id)


@pytest.mark.parametrize("rule_id, doc_type, text, citation, block_term", RULES)
def test_maker_and_checker_approve_grounded_citation_is_compliant(
    rule_id, doc_type, text, citation, block_term
):
    client = _ScriptedClient(_maker(citation), _checker())
    res = _evaluate(rule_id, doc_type, text, client)
    assert res["status"] == "COMPLIANT"
    assert res["checker_type"] == "MAKER_CHECKER"
    assert res["evidence"]["evidence_grounded"] is True
    assert client.calls == 2


@pytest.mark.parametrize("rule_id, doc_type, text, citation, block_term", RULES)
def test_checker_rejection_is_manual_review(rule_id, doc_type, text, citation, block_term):
    client = _ScriptedClient(_maker(citation), _checker(validation="REJECTED"))
    res = _evaluate(rule_id, doc_type, text, client)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"
    assert res["evidence"]["is_verified"] is False


@pytest.mark.parametrize("rule_id, doc_type, text, citation, block_term", RULES)
def test_citation_absent_from_document_is_manual_review(
    rule_id, doc_type, text, citation, block_term
):
    """Checker aprovou, mas a citacao do Maker nao existe no documento."""
    client = _ScriptedClient(_maker("CERTIDAO EMITIDA SEM RESSALVAS"), _checker())
    res = _evaluate(rule_id, doc_type, text, client)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"
    assert res["evidence"]["evidence_grounded"] is False


@pytest.mark.parametrize("rule_id, doc_type, text, citation, block_term", RULES)
def test_llm_unavailable_is_manual_review(rule_id, doc_type, text, citation, block_term):
    """Fail-closed: LLM indisponivel nunca aprova."""
    client = _ScriptedClient(LLMUnavailableError("provedor fora do ar"))
    res = _evaluate(rule_id, doc_type, text, client)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"
    assert res["evidence"]["error"] == "LLM_UNAVAILABLE"
    assert res["confidence_score"] == 0.0


@pytest.mark.parametrize("rule_id, doc_type, text, citation, block_term", RULES)
def test_block_term_is_non_compliant_without_calling_llm(
    rule_id, doc_type, text, citation, block_term
):
    client = _ScriptedClient(_maker(citation), _checker())
    res = _evaluate(rule_id, doc_type, f"{text}{block_term}\n", client)
    assert res["status"] == "NON_COMPLIANT"
    assert res["checker_type"] == "DETERMINISTIC"
    assert client.calls == 0


def test_rule_006_ceis_nada_consta_with_cnep_multa_aplicada_is_non_compliant():
    """CEIS 'nada consta' + 'multa aplicada' no CNEP reprova sem chamar o LLM."""
    client = _ScriptedClient(_maker("NADA CONSTA"), _checker())
    text = f"{_CEIS}\nNADA CONSTA\n{_CNEP}\nMULTA APLICADA: R$ 50.000,00\n"
    res = _evaluate("RULE-BNDES-006", "INTEGRIDADE_CEIS_CNEP", text, client)
    assert res["status"] == "NON_COMPLIANT"
    assert client.calls == 0


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Lacuna conhecida da RULE-BNDES-006: multa no CNEP sem a frase exata 'MULTA APLICADA' "
        "nao e bloqueada; o 'NADA CONSTA' do CEIS cumpre o termo obrigatorio e, com o "
        "Maker-Checker aprovando a citacao 'NADA CONSTA', hoje o resultado e COMPLIANT."
    ),
)
def test_rule_006_ceis_nada_consta_with_cnep_multa_in_other_words_is_not_compliant():
    client = _ScriptedClient(_maker("NADA CONSTA"), _checker())
    text = f"{_CEIS}\nNADA CONSTA\n{_CNEP}\nTIPO DE SANÇÃO: MULTA\nVALOR: R$ 50.000,00\n"
    res = _evaluate("RULE-BNDES-006", "INTEGRIDADE_CEIS_CNEP", text, client)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"

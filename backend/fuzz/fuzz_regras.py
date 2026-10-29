"""
Fuzzing do caminho de decisao (Atheris + libFuzzer).

Gera textos arbitrarios de documento e verifica invariantes de seguranca do produto, em vez de
apenas procurar excecoes:

1. Nenhuma entrada derruba a extracao de validade, o motor de regras ou a verificacao de citacao.
2. Fail-closed: com o LLM indisponivel, nenhuma regra avaliada pelo Maker-Checker sai COMPLIANT.
3. Certidao FISCAL ou TRABALHISTA so sai COMPLIANT com data de validade identificada.
4. O laudo geral so e COMPLIANT quando todas as regras aplicaveis sao COMPLIANT.
5. Toda citacao que e um trecho literal do documento e reconhecida como fundamentada, e toda
   citacao aceita aparece no documento normalizado.

Execucao (Linux, Python 3.12+, extra `fuzz` do backend):

    uv sync --frozen --package conformia-backend --extra fuzz --python 3.12
    uv run --python 3.12 python backend/fuzz/fuzz_regras.py -max_total_time=60

O LLM nunca e chamado: o Maker-Checker recebe um cliente sempre indisponivel.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Mesmos valores de teste do conftest: as configuracoes exigem esses campos, mas o fuzzing nao
# usa banco, fila, armazenamento nem autenticacao.
for _name, _value in {
    "SECRET_KEY": "fuzz-secret-key",
    "API_KEY": "fuzz-api-key",
    "POSTGRES_PASSWORD": "fuzz-postgres-password",
    "MINIO_ROOT_USER": "fuzz-minio-user",
    "MINIO_ROOT_PASSWORD": "fuzz-minio-password",
    "ENVIRONMENT": "test",
}.items():
    os.environ.setdefault(_name, _value)

from app.ai.llm_client import (  # noqa: E402
    LLMUnavailableError,
    MakerCheckerValidator,
    _normalize_for_match,
    is_grounded_in_document,
)
from app.services.rules_engine import (  # noqa: E402
    VALIDITY_REQUIRED_CATEGORIES,
    RulesEngine,
    summarize_statuses,
)

RULE_STATUSES = ["COMPLIANT", "NON_COMPLIANT", "MANUAL_REVIEW_REQUIRED", "NOT_APPLICABLE"]
OVERALL_STATUSES = {"COMPLIANT", "NON_COMPLIANT", "MANUAL_REVIEW_REQUIRED"}


class _UnavailableLLM:
    """Cliente que simula LLM indisponivel: exercita o caminho fail-closed sem rede."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise LLMUnavailableError("LLM desabilitado no fuzzing.")


ENGINE = RulesEngine(maker_checker=MakerCheckerValidator(client=_UnavailableLLM()))
DOCUMENT_TYPES: List[Optional[str]] = [None] + [rule["code"] for rule in ENGINE.rules]
CATEGORY_BY_RULE = {rule["id"]: rule["category"] for rule in ENGINE.rules}


def check(
    text: str,
    citation: str,
    slice_bounds: tuple[int, int],
    document_type: Optional[str],
    statuses: List[str],
) -> None:
    """Verifica as invariantes para uma entrada. Levanta AssertionError se alguma falhar."""
    ENGINE._extract_validity_date(text)

    evaluation = ENGINE.evaluate({"full_text": text}, document_type=document_type)
    assert evaluation["status"] in OVERALL_STATUSES, evaluation["status"]
    for result in evaluation["results"]:
        if result["status"] != "COMPLIANT":
            continue
        assert result["checker_type"] != "MAKER_CHECKER", f"LLM indisponivel aprovou {result}"
        if CATEGORY_BY_RULE[result["rule_id"]] in VALIDITY_REQUIRED_CATEGORIES:
            assert result.get("evidence", {}).get(
                "validity_date"
            ), f"aprovada sem validade: {result}"

    overall, score = summarize_statuses(statuses)
    applicable = [status for status in statuses if status != "NOT_APPLICABLE"]
    assert 0.0 <= score <= 1.0, score
    if overall == "COMPLIANT":
        assert applicable and all(status == "COMPLIANT" for status in applicable), statuses

    if is_grounded_in_document(citation, text):
        assert _normalize_for_match(citation) in _normalize_for_match(text), citation

    start, end = slice_bounds
    excerpt = text[start:end]
    if _normalize_for_match(excerpt):
        assert is_grounded_in_document(excerpt, text), (excerpt, text)


def test_one_input(data: bytes) -> None:
    import atheris

    provider = atheris.FuzzedDataProvider(data)
    text = provider.ConsumeUnicodeNoSurrogates(provider.ConsumeIntInRange(0, 4096))
    citation = provider.ConsumeUnicodeNoSurrogates(provider.ConsumeIntInRange(0, 128))
    start = provider.ConsumeIntInRange(0, len(text))
    end = provider.ConsumeIntInRange(start, len(text))
    document_type = provider.PickValueInList(DOCUMENT_TYPES)
    statuses = [
        provider.PickValueInList(RULE_STATUSES) for _ in range(provider.ConsumeIntInRange(0, 8))
    ]
    check(text, citation, (start, end), document_type, statuses)


def main() -> None:
    import atheris

    atheris.instrument_all()
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

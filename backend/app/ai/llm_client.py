"""LLM Client abstraction and Maker-Checker verification pipeline under Harness principles."""

import json
import logging
import re
import unicodedata
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

VALID_ASSESSMENTS = ("COMPLIANT", "NON_COMPLIANT", "MANUAL_REVIEW_REQUIRED")


class LLMUnavailableError(RuntimeError):
    """O provedor de LLM nao esta configurado ou nao respondeu de forma utilizavel."""


class LLMClient:
    """
    Abstração agnóstica de provedores de LLM.

    Sem chave configurada ou em caso de falha do provedor, levanta LLMUnavailableError.
    Nao existe resposta simulada: o chamador decide como degradar (revisao manual).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Executa a chamada ao modelo ou levanta LLMUnavailableError."""
        if not self.api_key:
            raise LLMUnavailableError("Chave de API LLM nao configurada.")

        try:
            # Integração padrão com OpenAI / provedores compatíveis
            import httpx

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": settings.LLM_TEMPERATURE,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            # O tipo da excecao basta para diagnostico; a mensagem pode ecoar a requisicao.
            logger.warning(f"Falha na chamada LLM externa: {type(e).__name__}.")
            raise LLMUnavailableError(
                f"Falha na chamada ao provedor LLM: {type(e).__name__}"
            ) from e


def _normalize_for_match(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("ASCII").upper()
    return re.sub(r"\s+", " ", ascii_text).strip()


def is_grounded_in_document(citation: Any, document_text: str) -> bool:
    """
    Verifica se a citacao do Maker aparece literalmente no documento (ignorando
    acentos, caixa e espacamento). Citacao vazia ou ausente nao fundamenta decisao.
    """
    if not isinstance(citation, str) or not citation.strip():
        return False
    return _normalize_for_match(citation) in _normalize_for_match(document_text)


class MakerCheckerValidator:
    """
    Padrão Maker-Checker para Harness Engineering:
    - Maker: avalia o documento e produz uma proposta de conformidade com evidências extraídas.
    - Checker: analisa independentemente se as evidências propostas pelo Maker realmente existem
      no documento original e se a regra foi aplicada estritamente sem alucinações.
    """

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or LLMClient()

    def evaluate_rule(self, rule_definition: Dict[str, Any], document_text: str) -> Dict[str, Any]:
        """
        Executa o ciclo Maker-Checker sob a regra e o texto do documento.

        Qualquer indisponibilidade do LLM, resposta malformada, avaliacao fora do dominio,
        rejeicao do Checker ou citacao que nao exista no documento resulta em
        MANUAL_REVIEW_REQUIRED. Nenhum desses caminhos pode produzir COMPLIANT.
        """
        try:
            return self._run_cycle(rule_definition, document_text)
        except LLMUnavailableError as exc:
            return {
                "rule_id": rule_definition.get("id"),
                "status": "MANUAL_REVIEW_REQUIRED",
                "error": "LLM_UNAVAILABLE",
                "reasoning": (
                    f"Avaliacao semantica nao executada ({exc}). "
                    "Regra encaminhada para revisao manual."
                ),
                "maker_output": None,
                "checker_output": None,
                "is_verified": False,
                "final_confidence": 0.0,
            }

    def _run_cycle(self, rule_definition: Dict[str, Any], document_text: str) -> Dict[str, Any]:
        document_excerpt = document_text[:3000]

        # Fase 1: O Maker analisa
        maker_system = (
            "Voce e o MAKER de conformidade documental do BNDES. Analise o texto e "
            "proponha uma avaliacao baseada estritamente nos dados presentes. "
            "Responda em JSON valido com as chaves: 'assessment' "
            "(COMPLIANT, NON_COMPLIANT, MANUAL_REVIEW_REQUIRED), "
            "'extracted_value' (citacao literal do trecho do documento que fundamenta a "
            "avaliacao), 'confidence', 'reasoning'."
        )
        maker_prompt = (
            f"REGRA:\n{json.dumps(rule_definition, indent=2, ensure_ascii=False)}\n\n"
            f"DOCUMENTO:\n{document_excerpt}"
        )
        maker_raw = self.client.generate(maker_prompt, system_prompt=maker_system)

        maker_result = _parse_json_object(maker_raw)
        if maker_result is None:
            maker_result = {
                "assessment": "MANUAL_REVIEW_REQUIRED",
                "extracted_value": None,
                "confidence": 0.5,
                "reasoning": "Nao foi possivel deserializar a resposta do Maker.",
            }

        # Fase 2: O Checker valida
        checker_system = (
            "Voce e o CHECKER auditor de conformidade documental do BNDES. Sua funcao e "
            "verificar se a proposta do MAKER e estritamente sustentada pelo texto original "
            "do documento, sem alucinacoes. Responda em JSON valido com: 'validation' "
            "('APPROVED', 'REJECTED'), 'critique', 'hallucination_detected' (bool), 'confidence'."
        )
        checker_prompt = (
            f"TEXTO DO DOCUMENTO:\n{document_excerpt}\n\n"
            f"PROPOSTA DO MAKER:\n{json.dumps(maker_result, indent=2, ensure_ascii=False)}"
        )
        checker_raw = self.client.generate(checker_prompt, system_prompt=checker_system)

        checker_result = _parse_json_object(checker_raw)
        if checker_result is None:
            checker_result = {
                "validation": "REJECTED",
                "critique": "Erro ao deserializar resposta do Checker.",
                "hallucination_detected": True,
                "confidence": 0.0,
            }

        # Sintese final: o Checker precisa aprovar sem alucinacao, a avaliacao do Maker
        # precisa estar no dominio e a citacao precisa existir literalmente no documento.
        assessment = maker_result.get("assessment")
        is_grounded = is_grounded_in_document(maker_result.get("extracted_value"), document_excerpt)
        is_approved = (
            checker_result.get("validation") == "APPROVED"
            and checker_result.get("hallucination_detected") is False
            and assessment in VALID_ASSESSMENTS
            and is_grounded
        )

        final_status = assessment if is_approved else "MANUAL_REVIEW_REQUIRED"

        final_confidence = (
            _as_confidence(maker_result.get("confidence"))
            + _as_confidence(checker_result.get("confidence"))
        ) / 2.0

        return {
            "rule_id": rule_definition.get("id"),
            "status": final_status,
            "maker_output": maker_result,
            "checker_output": checker_result,
            "evidence_grounded": is_grounded,
            "is_verified": is_approved,
            "final_confidence": round(final_confidence, 2) if is_approved else 0.0,
        }


def _parse_json_object(raw: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _as_confidence(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0:
        return float(value)
    return 0.0

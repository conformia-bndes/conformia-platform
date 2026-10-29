"""Deterministic and Hybrid Rules Engine for BNDES Document Compliance."""

from datetime import date
import json
import logging
import os
import re
import unicodedata
from typing import Callable, Dict, Any, List, Optional, Tuple

from app.ai.llm_client import MakerCheckerValidator

logger = logging.getLogger(__name__)

# Categorias cujas certidoes so comprovam regularidade dentro do prazo de validade.
VALIDITY_REQUIRED_CATEGORIES = ("FISCAL", "TRABALHISTA")


def summarize_statuses(statuses: List[str]) -> Tuple[str, float]:
    """
    Consolida os status das regras em (status geral, score). Regras NOT_APPLICABLE nao
    entram no calculo; sem nenhuma regra aplicavel o resultado e revisao manual.
    """
    applicable = [s for s in statuses if s != "NOT_APPLICABLE"]
    compliant = sum(1 for s in applicable if s == "COMPLIANT")
    score = (compliant / len(applicable)) if applicable else 0.0

    if "NON_COMPLIANT" in applicable:
        overall_status = "NON_COMPLIANT"
    elif "MANUAL_REVIEW_REQUIRED" in applicable or score < 1.0:
        overall_status = "MANUAL_REVIEW_REQUIRED"
    else:
        overall_status = "COMPLIANT"
    return overall_status, round(score, 2)


class RulesEngine:
    """
    Motor de regras deterministicas e hibridas:
    - Executa validacoes estritas baseadas em regex, palavras-chave e validade temporal.
    - Delega casos ambiguos para o orquestrador Maker-Checker de IA.
    - Suporta filtragem por tipologia documental para evitar avaliacoes indevidas.
    """

    def __init__(
        self,
        rules_file: Optional[str] = None,
        maker_checker: Optional[MakerCheckerValidator] = None,
        today: Callable[[], date] = date.today,
    ):
        self.rules_file = self._resolve_rules_file(rules_file)
        self.rules = self._load_rules()
        self.maker_checker = maker_checker or MakerCheckerValidator()
        self._today = today

    def _resolve_rules_file(self, rules_file: Optional[str]) -> str:
        """Resolve o caminho do arquivo de regras de forma resiliente."""
        candidates = [
            rules_file,
            os.getenv("RULES_FILE_PATH"),
            "/rules/schemas/bndes_sample_checklist.json",
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "..",
                    "rules",
                    "schemas",
                    "bndes_sample_checklist.json",
                )
            ),
            "rules/schemas/bndes_sample_checklist.json",
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return "rules/schemas/bndes_sample_checklist.json"

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Carrega regras declarativas a partir de arquivo JSON ou aplica checklist padrao."""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("rules", [])
            except Exception as e:
                logger.error(f"Erro ao carregar regras de {self.rules_file}: {e}")

        # Regras padrao de contingencia caso o arquivo nao seja localizado
        return [
            {
                "id": "RULE-BNDES-001",
                "code": "CND_FEDERAL",
                "title": "Certidao Negativa de Debitos Federais e Previdenciarios",
                "category": "FISCAL",
                "type": "DETERMINISTIC",
                "required_keywords": [
                    "CERTIDAO NEGATIVA",
                    "TRIBUTOS FEDERAIS",
                    "DIVIDA ATIVA DA UNIAO",
                ],
                "anti_keywords": ["CONSTA PENDENCIA", "DEBITOS EXISTENTES"],
                "regex_patterns": [
                    r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b",
                ],
                "requires_validity": True,
                "failure_message": "Documento nao comprova regularidade fiscal perante a Uniao.",
            },
            {
                "id": "RULE-BNDES-002",
                "code": "CRF_FGTS",
                "title": "Certificado de Regularidade do FGTS (CRF)",
                "category": "TRABALHISTA",
                "type": "DETERMINISTIC",
                "required_keywords": ["CERTIFICADO DE REGULARIDADE", "FGTS", "REGULAR"],
                "anti_keywords": ["IRREGULAR"],
                "regex_patterns": [
                    r"CRF\d{8,14}",
                ],
                "requires_validity": True,
                "failure_message": "Comprovante de regularidade do FGTS ausente ou invalido.",
            },
        ]

    def _extract_validity_date(self, text: str) -> Optional[date]:
        """Extrai data de validade ou vigencia do texto da certidao."""
        patterns = [
            (
                r"(?:v[aá]lid[ao]\s+at[eé]|validade|vig[eê]ncia|data\s+de\s+validade)"
                r"[\s:]+(\d{2})[/\-.](\d{2})[/\-.](\d{4})"
            ),
            r"at[eé]\s+(\d{2})[/\-.](\d{2})[/\-.](\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day, month, year = match.groups()
                try:
                    return date(int(year), int(month), int(day))
                except ValueError:
                    continue
        return None

    def evaluate(
        self,
        extracted_data: Dict[str, Any],
        target_category: Optional[str] = None,
        target_rule_ids: Optional[List[str]] = None,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Avalia o texto e metadados extraidos contra as regras pertinentes.

        Quando `document_type` e informado, somente as regras cujo `code` corresponde a
        tipologia identificada sao avaliadas; as demais ficam NOT_APPLICABLE. Sem esse
        filtro, uma CND valida seria reprovada por nao ser, por exemplo, um CRF do FGTS.
        """
        full_text = extracted_data.get("full_text", "")
        results: List[Dict[str, Any]] = []
        evaluated_rules = 0
        compliant_count = 0

        for rule in self.rules:
            # Filtragem por categoria ou lista de IDs de regras
            if target_category and rule.get("category") != target_category:
                results.append(
                    self._not_applicable(
                        rule, "Regra nao aplicavel a tipologia documental informada."
                    )
                )
                continue

            if document_type and rule.get("code") != document_type:
                results.append(
                    self._not_applicable(
                        rule,
                        f"Regra aplicavel a tipologia {rule.get('code')}; "
                        f"documento identificado como {document_type}.",
                    )
                )
                continue

            if target_rule_ids and rule.get("id") not in target_rule_ids:
                continue

            evaluated_rules += 1
            result = self._evaluate_single_rule(rule, full_text, extracted_data)
            results.append(result)
            if result.get("status") == "COMPLIANT":
                compliant_count += 1

        overall_status, score = summarize_statuses([r["status"] for r in results])

        return {
            "status": overall_status,
            "overall_status": overall_status,
            "document_type": document_type,
            "compliance_score": score,
            "total_rules": len(results),
            "evaluated_rules": evaluated_rules,
            "compliant_rules": compliant_count,
            "results": results,
            "checks": results,
        }

    def not_evaluable(self, reason: str) -> Dict[str, Any]:
        """
        Resultado para documentos que nao podem ser avaliados (ex.: tipologia nao
        identificada). Nenhuma regra e aplicada e o laudo fica em revisao manual:
        a ausencia de avaliacao nunca equivale a conformidade.
        """
        results = [self._not_applicable(rule, reason) for rule in self.rules]
        return {
            "status": "MANUAL_REVIEW_REQUIRED",
            "overall_status": "MANUAL_REVIEW_REQUIRED",
            "document_type": None,
            "findings": reason,
            "compliance_score": 0.0,
            "total_rules": len(results),
            "evaluated_rules": 0,
            "compliant_rules": 0,
            "results": results,
            "checks": results,
        }

    @staticmethod
    def _not_applicable(rule: Dict[str, Any], findings: str) -> Dict[str, Any]:
        return {
            "rule_id": rule["id"],
            "rule_title": rule["title"],
            "category": rule["category"],
            "status": "NOT_APPLICABLE",
            "findings": findings,
            "confidence_score": 1.0,
            "checker_type": "DETERMINISTIC",
        }

    def _normalize(self, text: str) -> str:
        """Normaliza texto removendo acentos para comparacoes textuais robustas."""
        nfkd = unicodedata.normalize("NFKD", text)
        return nfkd.encode("ASCII", "ignore").decode("ASCII").upper()

    def _evaluate_single_rule(
        self, rule: Dict[str, Any], full_text: str, extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Avalia uma regra individual aplicando checagem deterministica, regex e temporal."""
        text_norm = self._normalize(full_text)
        rule_type = rule.get("type", "DETERMINISTIC")

        # 1. Avaliacao de palavras-chave excludentes (anti-keywords)
        anti_keywords = rule.get("anti_keywords", [])
        matched_anti = [kw for kw in anti_keywords if self._normalize(kw) in text_norm]
        if matched_anti:
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "NON_COMPLIANT",
                "findings": f"Termos restritivos no texto: {', '.join(matched_anti)}",
                "confidence_score": 1.0,
                "checker_type": "DETERMINISTIC",
                "evidence": {"matched_anti_keywords": matched_anti},
            }

        # 2. Avaliacao de palavras-chave requeridas
        required_keywords = rule.get("required_keywords", [])
        matched_required = [kw for kw in required_keywords if self._normalize(kw) in text_norm]
        all_required_met = (
            len(matched_required) == len(required_keywords) if required_keywords else False
        )

        if not all_required_met:
            missing = list(set(required_keywords) - set(matched_required))
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "NON_COMPLIANT",
                "findings": rule.get("failure_message", "Criterios minimos nao encontrados."),
                "confidence_score": 0.9,
                "checker_type": "DETERMINISTIC",
                "evidence": {"missing_keywords": missing},
            }

        # 3. Avaliacao de regex_patterns
        regex_patterns = rule.get("regex_patterns", [])
        matched_patterns = []
        for pattern in regex_patterns:
            try:
                if re.search(pattern, full_text, re.IGNORECASE):
                    matched_patterns.append(pattern)
            except re.error as re_err:
                logger.warning(f"Padrao regex invalido na regra {rule['id']}: {pattern} - {re_err}")

        # 4. Verificacao de validade temporal (Diretriz no 1 do AGENTS.md): sem data de
        # validade legivel, a certidao nunca e aprovada automaticamente.
        requires_validity = rule.get(
            "requires_validity", rule.get("category") in VALIDITY_REQUIRED_CATEGORIES
        )
        validity_date = self._extract_validity_date(full_text)

        if validity_date:
            # Comparacao por data: a certidao vale ate o fim do dia de validade.
            if validity_date < self._today():
                return {
                    "rule_id": rule["id"],
                    "rule_title": rule["title"],
                    "category": rule["category"],
                    "status": "NON_COMPLIANT",
                    "findings": (f"Certidao expirada em " f"{validity_date.strftime('%d/%m/%Y')}."),
                    "confidence_score": 1.0,
                    "checker_type": "DETERMINISTIC",
                    "evidence": {
                        "validity_date": validity_date.strftime("%d/%m/%Y"),
                        "matched_keywords": matched_required,
                    },
                }
        elif requires_validity:
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "MANUAL_REVIEW_REQUIRED",
                "findings": (
                    "Data de validade da certidao nao identificada de forma legivel. "
                    "Necessita revisao manual por analista BNDES."
                ),
                "confidence_score": 0.6,
                "checker_type": "DETERMINISTIC",
                "evidence": {"matched_keywords": matched_required},
            }

        # Determinístico aprovado
        if rule_type == "DETERMINISTIC":
            evidence_data: Dict[str, Any] = {"matched_keywords": matched_required}
            if matched_patterns:
                evidence_data["matched_regex_patterns"] = matched_patterns
            if validity_date:
                evidence_data["validity_date"] = validity_date.strftime("%d/%m/%Y")

            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "COMPLIANT",
                "findings": "Todos os criterios deterministicos de conformidade foram atendidos.",
                "confidence_score": 1.0,
                "checker_type": "DETERMINISTIC",
                "evidence": evidence_data,
            }

        # Regra HIBRIDA / SEMANTICA: Se o deterministico deu positivo, valida com Maker-Checker
        harness_result = self.maker_checker.evaluate_rule(rule, full_text)
        reasoning = (harness_result.get("maker_output") or {}).get(
            "reasoning"
        ) or harness_result.get("reasoning", "")
        return {
            "rule_id": rule["id"],
            "rule_title": rule["title"],
            "category": rule["category"],
            "status": harness_result.get("status", "MANUAL_REVIEW_REQUIRED"),
            "findings": f"Avaliacao Maker-Checker: {reasoning}",
            "confidence_score": harness_result.get("final_confidence", 0.0),
            "checker_type": "MAKER_CHECKER",
            "evidence": harness_result,
        }

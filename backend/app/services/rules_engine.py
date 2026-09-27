"""Deterministic and Hybrid Rules Engine for BNDES Document Compliance."""

from datetime import datetime
import json
import logging
import os
import re
import unicodedata
from typing import Dict, Any, List, Optional

from app.ai.llm_client import MakerCheckerValidator

logger = logging.getLogger(__name__)


class RulesEngine:
    """
    Motor de regras deterministicas e hibridas:
    - Executa validacoes estritas baseadas em regex, palavras-chave e validade temporal.
    - Delega casos ambiguos para o orquestrador Maker-Checker de IA.
    - Suporta filtragem por tipologia documental para evitar avaliacoes indevidas.
    """

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = self._resolve_rules_file(rules_file)
        self.rules = self._load_rules()
        self.maker_checker = MakerCheckerValidator()

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

    def _extract_validity_date(self, text: str) -> Optional[datetime]:
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
                    return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
        return None

    def evaluate(
        self,
        extracted_data: Dict[str, Any],
        target_category: Optional[str] = None,
        target_rule_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Avalia o texto e metadados extraidos contra as regras pertinentes.
        """
        full_text = extracted_data.get("full_text", "")
        results: List[Dict[str, Any]] = []
        evaluated_rules = 0
        compliant_count = 0

        for rule in self.rules:
            # Filtragem por categoria ou lista de IDs de regras
            if target_category and rule.get("category") != target_category:
                results.append(
                    {
                        "rule_id": rule["id"],
                        "rule_title": rule["title"],
                        "category": rule["category"],
                        "status": "NOT_APPLICABLE",
                        "findings": "Regra nao aplicavel a tipologia documental informada.",
                        "confidence_score": 1.0,
                        "checker_type": "DETERMINISTIC",
                    }
                )
                continue

            if target_rule_ids and rule.get("id") not in target_rule_ids:
                continue

            evaluated_rules += 1
            result = self._evaluate_single_rule(rule, full_text, extracted_data)
            results.append(result)
            if result.get("status") == "COMPLIANT":
                compliant_count += 1

        score = (compliant_count / evaluated_rules) if evaluated_rules > 0 else 0.0

        has_non_compliant = any(r["status"] == "NON_COMPLIANT" for r in results)
        has_manual_review = any(r["status"] == "MANUAL_REVIEW_REQUIRED" for r in results)

        if has_non_compliant:
            overall_status = "NON_COMPLIANT"
        elif has_manual_review or score < 1.0:
            overall_status = "MANUAL_REVIEW_REQUIRED"
        else:
            overall_status = "COMPLIANT"

        return {
            "status": overall_status,
            "overall_status": overall_status,
            "compliance_score": round(score, 2),
            "total_rules": len(results),
            "evaluated_rules": evaluated_rules,
            "compliant_rules": compliant_count,
            "results": results,
            "checks": results,
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

        # 4. Verificacao de validade temporal (Diretriz no 1 do AGENTS.md)
        requires_validity = rule.get("requires_validity", False) or rule.get("category") in (
            "FISCAL",
            "TRABALHISTA",
        )
        validity_date = self._extract_validity_date(full_text)

        if validity_date:
            today = datetime.now()
            if validity_date < today:
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
        elif requires_validity and rule.get("strict_validity", False):
            # Se a certidao exige data estrita e nao contem de forma legivel
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
        return {
            "rule_id": rule["id"],
            "rule_title": rule["title"],
            "category": rule["category"],
            "status": harness_result.get("status", "MANUAL_REVIEW_REQUIRED"),
            "findings": (
                f"Avaliacao Maker-Checker: "
                f"{harness_result.get('maker_output', {}).get('reasoning', '')}"
            ),
            "confidence_score": harness_result.get("final_confidence", 0.8),
            "checker_type": "MAKER_CHECKER",
            "evidence": harness_result,
        }

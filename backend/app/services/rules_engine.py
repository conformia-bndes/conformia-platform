"""Deterministic and Hybrid Rules Engine for BNDES Document Compliance."""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from app.ai.llm_client import MakerCheckerValidator

logger = logging.getLogger(__name__)


class RulesEngine:
    """
    Motor de regras determinísticas e híbridas:
    - Executa validações estritas baseadas em regex, palavras-chave e datas.
    - Delega casos ambíguos para o orquestrador Maker-Checker de IA.
    """

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file or os.getenv("RULES_FILE_PATH", "rules/schemas/bndes_sample_checklist.json")
        self.rules = self._load_rules()
        self.maker_checker = MakerCheckerValidator()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Carrega regras declarativas a partir de arquivo JSON ou aplica checklist padrão."""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("rules", [])
            except Exception as e:
                logger.error(f"Erro ao carregar regras de {self.rules_file}: {e}")

        # Regras padrão caso o arquivo não seja encontrado
        return [
            {
                "id": "RULE-BNDES-001",
                "code": "CND_FEDERAL",
                "title": "Certidão Negativa de Débitos Federais e Previdenciários",
                "category": "FISCAL",
                "type": "DETERMINISTIC",
                "required_keywords": ["CERTIDÃO NEGATIVA", "TRIBUTOS FEDERAIS", "DÍVIDA ATIVA DA UNIÃO"],
                "anti_keywords": ["CONSTA PENDÊNCIA", "DÉBITOS EXISTENTES"],
                "failure_message": "Documento não comprova regularidade fiscal perante a União."
            },
            {
                "id": "RULE-BNDES-002",
                "code": "CRF_FGTS",
                "title": "Certificado de Regularidade do FGTS (CRF)",
                "category": "TRABALHISTA",
                "type": "DETERMINISTIC",
                "required_keywords": ["CERTIFICADO DE REGULARIDADE", "FGTS", "REGULAR"],
                "anti_keywords": ["IRREGULAR"],
                "failure_message": "Comprovante de regularidade do FGTS ausente ou inválido."
            },
            {
                "id": "RULE-BNDES-003",
                "code": "FALENCIA_CONCORDATA",
                "title": "Certidão Negativa de Falência e Recuperação Judicial",
                "category": "JURIDICA",
                "type": "HYBRID",
                "required_keywords": ["FALÊNCIA", "RECUPERAÇÃO JUDICIAL", "NADA CONSTA"],
                "failure_message": "Certidão aponta existência de processo de falência ou recuperação."
            }
        ]

    def evaluate(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia o texto e metadados extraídos contra o conjunto de regras ativas.
        """
        full_text = extracted_data.get("full_text", "")
        results: List[Dict[str, Any]] = []
        compliant_count = 0

        for rule in self.rules:
            result = self._evaluate_single_rule(rule, full_text, extracted_data)
            results.append(result)
            if result.get("status") == "COMPLIANT":
                compliant_count += 1

        total_rules = len(self.rules)
        score = (compliant_count / total_rules) if total_rules > 0 else 0.0

        overall_status = "COMPLIANT" if score == 1.0 else (
            "NON_COMPLIANT" if any(r["status"] == "NON_COMPLIANT" for r in results) else "MANUAL_REVIEW_REQUIRED"
        )

        return {
            "status": overall_status,
            "compliance_score": round(score, 2),
            "total_rules": total_rules,
            "compliant_rules": compliant_count,
            "results": results
        }

    def _evaluate_single_rule(
        self,
        rule: Dict[str, Any],
        full_text: str,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Avalia uma regra individual aplicando checagem determinística ou híbrida."""
        text_upper = full_text.upper()
        rule_type = rule.get("type", "DETERMINISTIC")

        # Avaliação de palavras-chave requeridas
        required_keywords = [kw.upper() for kw in rule.get("required_keywords", [])]
        matched_required = [kw for kw in required_keywords if kw in text_upper]

        # Avaliação de palavras-chave excludentes (anti-keywords)
        anti_keywords = [kw.upper() for kw in rule.get("anti_keywords", [])]
        matched_anti = [kw for kw in anti_keywords if kw in text_upper]

        # Se anti-keywords forem encontradas, é violação direta
        if matched_anti:
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "NON_COMPLIANT",
                "findings": f"Identificados termos restritivos no texto: {', '.join(matched_anti)}",
                "confidence_score": 1.0,
                "checker_type": "DETERMINISTIC",
                "evidence": {"matched_anti_keywords": matched_anti}
            }

        # Determinístico puro
        all_required_met = len(matched_required) == len(required_keywords) if required_keywords else False

        if rule_type == "DETERMINISTIC":
            if all_required_met:
                return {
                    "rule_id": rule["id"],
                    "rule_title": rule["title"],
                    "category": rule["category"],
                    "status": "COMPLIANT",
                    "findings": "Todos os critérios determinísticos de conformidade foram localizados.",
                    "confidence_score": 1.0,
                    "checker_type": "DETERMINISTIC",
                    "evidence": {"matched_keywords": matched_required}
                }
            else:
                return {
                    "rule_id": rule["id"],
                    "rule_title": rule["title"],
                    "category": rule["category"],
                    "status": "NON_COMPLIANT",
                    "findings": rule.get("failure_message", "Critérios mínimos não encontrados."),
                    "confidence_score": 0.9,
                    "checker_type": "DETERMINISTIC",
                    "evidence": {"missing_keywords": list(set(required_keywords) - set(matched_required))}
                }

        # Regra HÍBRIDA / SEMÂNTICA: Se o determinístico deu positivo, valida com Maker-Checker
        if all_required_met:
            harness_result = self.maker_checker.evaluate_rule(rule, full_text)
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": harness_result.get("status", "MANUAL_REVIEW_REQUIRED"),
                "findings": (
                    f"Avaliação Maker-Checker: {harness_result.get('maker_output', {}).get('reasoning', '')}"
                ),
                "confidence_score": harness_result.get("final_confidence", 0.8),
                "checker_type": "MAKER_CHECKER",
                "evidence": harness_result
            }

        return {
            "rule_id": rule["id"],
            "rule_title": rule["title"],
            "category": rule["category"],
            "status": "MANUAL_REVIEW_REQUIRED",
            "findings": "Evidências textuais parciais. Necessita verificação humana supervisionada.",
            "confidence_score": 0.5,
            "checker_type": "HYBRID",
            "evidence": {"matched_keywords": matched_required}
        }

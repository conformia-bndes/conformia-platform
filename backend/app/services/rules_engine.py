"""Deterministic and Hybrid Rules Engine for BNDES Document Compliance."""

from datetime import date
import json
import logging
import os
import re
import unicodedata
from typing import Callable, Dict, Any, List, Optional, Tuple

from app.ai.llm_client import MakerCheckerValidator
from app.idp.parser import scan_validity_dates

logger = logging.getLogger(__name__)

# Categorias cujas certidoes so comprovam regularidade dentro do prazo de validade.
VALIDITY_REQUIRED_CATEGORIES = ("FISCAL", "TRABALHISTA")

# Prefixos imediatos que negam um termo impeditivo positivo (ex.: "NAO CONSTAM DEBITOS").
_NEGATION_PREFIX_RE = re.compile(
    r"(?:^|\b)(?:NAO(?:\s+(?:CONSTAM?|EXISTEM?|HA|POSSUI))?|NENHUM[A]?|SEM|INEXISTENCIA\s+DE)\s+$"
)


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
        """
        Retorna a data de validade quando inequivoca (ou a data vencida mais antiga),
        delegando a leitura a `scan_validity_dates` (fonte unica com o parser IDP).
        """
        scan = scan_validity_dates(text)
        today = self._today()
        expired = [d for d in scan.valid_dates if d < today]
        if expired:
            return min(expired)
        if len(scan.valid_dates) == 1 and not scan.invalid_raw_dates:
            return scan.valid_dates[0]
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

    def _strip_accents(self, text: str) -> str:
        """Remove acentos preservando caixa (seguro para metacaracteres regex como \\b)."""
        nfkd = unicodedata.normalize("NFKD", text)
        return nfkd.encode("ASCII", "ignore").decode("ASCII")

    def _normalize(self, text: str) -> str:
        """Normaliza texto removendo acentos, colapsando espacos e convertendo para maiusculas."""
        ascii_text = self._strip_accents(text).upper()
        return re.sub(r"\s+", " ", ascii_text).strip()

    def _matches_anti_keyword(self, keyword: str, text_norm: str) -> bool:
        """
        Verifica se um termo impeditivo ocorre de forma nao negada no texto normalizado.
        Evita falso negativo/positivo em frases como "NAO CONSTAM DEBITOS" quando o termo
        configurado e "CONSTAM DEBITOS", mantendo correspondencia direta para termos que
        ja contem negacao (ex.: "NAO HABILITADO").
        """
        kw_norm = self._normalize(keyword)
        if not kw_norm:
            return False
        pattern = re.compile(r"(?<!\w)" + re.escape(kw_norm) + r"(?!\w)")
        starts_with_negation = kw_norm.startswith(("NAO ", "SEM "))
        for match in pattern.finditer(text_norm):
            if starts_with_negation:
                return True
            prefix = text_norm[max(0, match.start() - 32) : match.start()]
            if _NEGATION_PREFIX_RE.search(prefix):
                continue
            return True
        return False

    def _evaluate_single_rule(
        self, rule: Dict[str, Any], full_text: str, extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Avalia uma regra individual aplicando checagem deterministica, temporal e regex."""
        text_norm = self._normalize(full_text)
        text_ascii_compact = re.sub(r"\s+", " ", self._strip_accents(full_text)).strip()
        rule_type = rule.get("type", "DETERMINISTIC")

        # 1. Avaliacao de palavras-chave excludentes (anti-keywords)
        anti_keywords = rule.get("anti_keywords", [])
        matched_anti = [kw for kw in anti_keywords if self._matches_anti_keyword(kw, text_norm)]
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

        # 1b. Termos que exigem analise humana (ex.: sancao descrita sem a frase exata de um
        # anti_keyword). Nao provam irregularidade, mas impedem a aprovacao automatica.
        manual_review_keywords = rule.get("manual_review_keywords", [])
        matched_manual = [kw for kw in manual_review_keywords if self._normalize(kw) in text_norm]
        if matched_manual:
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "MANUAL_REVIEW_REQUIRED",
                "findings": (
                    "Termos que exigem analise humana no texto: " f"{', '.join(matched_manual)}"
                ),
                "confidence_score": 1.0,
                "checker_type": "DETERMINISTIC",
                "evidence": {"matched_manual_review_keywords": matched_manual},
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
                # Decisao D2: a falta de um termo obrigatorio (ex.: OCR ilegivel) nao prova
                # irregularidade; o analista decide. Termos impeditivos seguem NON_COMPLIANT.
                "status": "MANUAL_REVIEW_REQUIRED",
                "findings": rule.get("failure_message", "Criterios minimos nao encontrados."),
                "confidence_score": 0.9,
                "checker_type": "DETERMINISTIC",
                "evidence": {"missing_keywords": missing},
            }

        # 3. Verificacao de validade temporal (fonte unica com parser IDP; AGENTS.md diretriz 1).
        # Qualquer data vencida reprova; multiplas datas vigentes distintas, datas impossiveis
        # ou ausencia de validade (quando exigida) encaminham para revisao manual.
        requires_validity = rule.get(
            "requires_validity", rule.get("category") in VALIDITY_REQUIRED_CATEGORIES
        )
        validity_scan = scan_validity_dates(full_text)
        today = self._today()
        expired_dates = [d for d in validity_scan.valid_dates if d < today]
        valid_date: Optional[date] = None

        if expired_dates:
            earliest_expired = min(expired_dates)
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "NON_COMPLIANT",
                "findings": (f"Certidao expirada em {earliest_expired.strftime('%d/%m/%Y')}."),
                "confidence_score": 1.0,
                "checker_type": "DETERMINISTIC",
                "evidence": {
                    "validity_date": earliest_expired.strftime("%d/%m/%Y"),
                    "validity_dates": [d.strftime("%d/%m/%Y") for d in validity_scan.valid_dates],
                    "expired_dates": [d.strftime("%d/%m/%Y") for d in expired_dates],
                    "matched_keywords": matched_required,
                },
            }

        if requires_validity:
            if not validity_scan.valid_dates:
                evidence_missing: Dict[str, Any] = {"matched_keywords": matched_required}
                if validity_scan.invalid_raw_dates:
                    evidence_missing["invalid_validity_dates"] = list(
                        validity_scan.invalid_raw_dates
                    )
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
                    "evidence": evidence_missing,
                }
            if len(validity_scan.valid_dates) > 1 or validity_scan.invalid_raw_dates:
                evidence_ambiguous: Dict[str, Any] = {
                    "matched_keywords": matched_required,
                    "validity_dates": [d.strftime("%d/%m/%Y") for d in validity_scan.valid_dates],
                }
                if validity_scan.invalid_raw_dates:
                    evidence_ambiguous["invalid_validity_dates"] = list(
                        validity_scan.invalid_raw_dates
                    )
                return {
                    "rule_id": rule["id"],
                    "rule_title": rule["title"],
                    "category": rule["category"],
                    "status": "MANUAL_REVIEW_REQUIRED",
                    "findings": (
                        "Multiplas datas de validade distintas ou data invalida identificadas "
                        "no documento. Necessita revisao manual por analista BNDES."
                    ),
                    "confidence_score": 0.6,
                    "checker_type": "DETERMINISTIC",
                    "evidence": evidence_ambiguous,
                }
            valid_date = validity_scan.valid_dates[0]
        elif len(validity_scan.valid_dates) == 1 and not validity_scan.invalid_raw_dates:
            valid_date = validity_scan.valid_dates[0]

        # 4. Validacao obrigatoria de regex_patterns (ex.: CNPJ, numero CRF).
        # Ausencia de padrao estrutural nao prova irregularidade, mas impede aprovacao
        # automatica e encaminha para revisao manual (politica D2).
        regex_patterns = rule.get("regex_patterns", [])
        matched_patterns: List[str] = []
        missing_patterns: List[str] = []
        for pattern in regex_patterns:
            try:
                pattern_ascii = self._strip_accents(pattern)
                if re.search(pattern, full_text, re.IGNORECASE) or re.search(
                    pattern_ascii, text_ascii_compact, re.IGNORECASE
                ):
                    matched_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)
            except re.error as re_err:
                logger.warning(f"Padrao regex invalido na regra {rule['id']}: {pattern} - {re_err}")
                missing_patterns.append(pattern)

        if missing_patterns:
            evidence_regex: Dict[str, Any] = {
                "matched_keywords": matched_required,
                "matched_regex_patterns": matched_patterns,
                "missing_regex_patterns": missing_patterns,
            }
            if valid_date:
                evidence_regex["validity_date"] = valid_date.strftime("%d/%m/%Y")
            return {
                "rule_id": rule["id"],
                "rule_title": rule["title"],
                "category": rule["category"],
                "status": "MANUAL_REVIEW_REQUIRED",
                "findings": (
                    "Padroes estruturais obrigatorios nao identificados no documento "
                    "(ex.: CNPJ ou identificador da certidao). Necessita revisao manual."
                ),
                "confidence_score": 0.8,
                "checker_type": "DETERMINISTIC",
                "evidence": evidence_regex,
            }

        # Determinístico aprovado
        if rule_type == "DETERMINISTIC":
            evidence_data: Dict[str, Any] = {"matched_keywords": matched_required}
            if matched_patterns:
                evidence_data["matched_regex_patterns"] = matched_patterns
            if valid_date:
                evidence_data["validity_date"] = valid_date.strftime("%d/%m/%Y")

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

"""Regression and Evaluation Pipeline for Document Extraction & Compliance Rules.

Cada caso percorre o mesmo caminho do produto: deteccao da tipologia pelo parser IDP
e avaliacao somente das regras daquela tipologia. Casos vem de duas fontes: a lista
BENCHMARK_CASES abaixo e os arquivos JSON em evals/datasets/.

Limite de interpretacao: os casos sao textos sinteticos de poucas certidoes. Eles detectam
regressoes de regra deterministica; nao medem a qualidade de OCR nem do LLM.
"""

import glob
import json
import os
import sys
import time
from datetime import date
from typing import List, Dict, Any

# Garante suporte a UTF-8 no console do Windows/Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Adiciona o backend ao path para importação dos módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

# O benchmark nao usa banco, fila nem storage; valores descartaveis apenas satisfazem a
# validacao de Settings no import (segredos nao possuem default no codigo).
for _name in ("SECRET_KEY", "API_KEY", "POSTGRES_PASSWORD", "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"):
    os.environ.setdefault(_name, "eval-only")

from app.idp.parser import extract_fields_and_evidence  # noqa: E402
from app.services.rules_engine import RulesEngine  # noqa: E402

EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(EVALS_DIR, "..", "rules", "schemas", "bndes_sample_checklist.json")
# Data de referencia fixa: o resultado do benchmark nao depende do dia em que roda.
REFERENCE_DATE = date(2026, 10, 29)
ACCURACY_THRESHOLD = 90.0


# Casos de teste de referência com Ground Truth
BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "id": "CASE-001",
        "description": "CND Federal - Certidão Limpa, Regular e Vigente",
        "input_text": (
            "REPÚBLICA FEDERATIVA DO BRASIL - MINISTÉRIO DA FAZENDA\n"
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "É certificado que não constam pendências em nome do sujeito passivo.\n"
            "Válida até: 31/12/2026"
        ),
        "expected_results": {
            "RULE-BNDES-001": "COMPLIANT"
        }
    },
    {
        "id": "CASE-002",
        "description": "CND Federal com Débitos Ativos (Tentativa de Fraude/Não Conforme)",
        "input_text": (
            "SECRETARIA DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDÃO POSITIVA - CONSTA PENDÊNCIA RELATIVA AOS TRIBUTOS FEDERAIS E DÍVIDA ATIVA\n"
            "CNPJ: 98.765.432/0001-11"
        ),
        "expected_results": {
            "RULE-BNDES-001": "NON_COMPLIANT"
        }
    },
    {
        "id": "CASE-003",
        "description": "CRF FGTS Regular e Vigente",
        "input_text": (
            "CAIXA ECONÔMICA FEDERAL\n"
            "CERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
            "Inscrição: 12.345.678/0001-90\n"
            "A Caixa Econômica Federal certifica que a empresa encontra-se em SITUAÇÃO REGULAR.\n"
            "Validade: 15/11/2026"
        ),
        "expected_results": {
            "RULE-BNDES-002": "COMPLIANT"
        }
    },
    {
        "id": "CASE-004",
        "description": "Falência Decretada (Violação Crítica de Integridade Financeira)",
        "input_text": (
            "TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO\n"
            "CERTIDÃO DOS DISTRIBUIDORES CÍVEIS\n"
            "CONSTA DISTRIBUIÇÃO DE PROCESSO DE FALÊNCIA E RECUPERAÇÃO JUDICIAL"
        ),
        "expected_results": {
            "RULE-BNDES-004": "NON_COMPLIANT"
        }
    },
    {
        "id": "CASE-005",
        "description": "CND Federal com Validade Expirada (Não Conforme Temporal)",
        "input_text": (
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "É certificado que não constam pendências em nome do sujeito passivo.\n"
            "Válida até: 01/01/2020"
        ),
        "expected_results": {
            "RULE-BNDES-001": "NON_COMPLIANT"
        }
    },
    {
        "id": "CASE-006",
        "description": "CND Federal sem Data de Validade Legível (AGENTS.md, diretriz 1)",
        "input_text": (
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "É certificado que não constam pendências em nome do sujeito passivo."
        ),
        "expected_results": {
            "RULE-BNDES-001": "MANUAL_REVIEW_REQUIRED"
        }
    },
    {
        "id": "CASE-007",
        "description": "CRF FGTS Regular sem Data de Validade",
        "input_text": (
            "CAIXA ECONÔMICA FEDERAL\n"
            "CERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
            "A Caixa Econômica Federal certifica que a empresa encontra-se em SITUAÇÃO REGULAR."
        ),
        "expected_results": {
            "RULE-BNDES-002": "MANUAL_REVIEW_REQUIRED"
        }
    },
    {
        "id": "CASE-008",
        "description": "CND Federal válida não é reprovada por regras de outras tipologias",
        "input_text": (
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO\n"
            "Válida até: 31/12/2026"
        ),
        "expected_results": {
            "RULE-BNDES-001": "COMPLIANT",
            "RULE-BNDES-002": "NOT_APPLICABLE",
            "RULE-BNDES-004": "NOT_APPLICABLE"
        },
        "expected_overall": "COMPLIANT"
    },
]


def load_dataset_cases() -> List[Dict[str, Any]]:
    """Converte os arquivos JSON de evals/datasets/ para o formato de BENCHMARK_CASES."""
    cases = []
    pattern = os.path.join(EVALS_DIR, "datasets", "*", "*.json")
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as f:
            sample = json.load(f)
        cases.append(
            {
                "id": sample["id"],
                "description": f"Dataset {os.path.relpath(path, EVALS_DIR)}",
                "input_text": sample["text"],
                "expected_results": {sample["expected_rule"]: sample["expected_status"]},
            }
        )
    return cases


def evaluate_like_product(engine: RulesEngine, text: str) -> Dict[str, Any]:
    """Reproduz o fluxo do produto: tipologia detectada pelo parser, regras filtradas."""
    document_type = extract_fields_and_evidence(text).document_type
    if document_type is None:
        return engine.not_evaluable("Tipologia documental nao identificada.")
    return engine.evaluate({"full_text": text, "metadata": {}}, document_type=document_type)


def run_evaluation() -> bool:
    print("=" * 70)
    print("Conform.IA BNDES - Pipeline de Avaliacao Continua (Evals)")
    print(f"Data de referencia: {REFERENCE_DATE.isoformat()}")
    print("=" * 70)

    engine = RulesEngine(rules_file=RULES_FILE, today=lambda: REFERENCE_DATE)
    total_checks = 0
    passed_checks = 0
    false_positives = 0
    start_time = time.time()

    for case in BENCHMARK_CASES + load_dataset_cases():
        print(f"\n[EVAL] Executando {case['id']}: {case['description']}")
        eval_result = evaluate_like_product(engine, case["input_text"])
        print(f"  Tipologia detectada: {eval_result['document_type']}")

        # Mapeia resultados por rule_id
        actual_by_rule = {r["rule_id"]: r["status"] for r in eval_result["results"]}
        expectations = dict(case["expected_results"])
        if "expected_overall" in case:
            actual_by_rule["OVERALL"] = eval_result["overall_status"]
            expectations["OVERALL"] = case["expected_overall"]

        for rule_id, expected_status in expectations.items():
            total_checks += 1
            actual_status = actual_by_rule.get(rule_id, "NOT_EVALUATED")

            # Falso Positivo: qualquer aprovacao (COMPLIANT) onde a verdade nao era COMPLIANT
            if expected_status != "COMPLIANT" and actual_status == "COMPLIANT":
                false_positives += 1
                print(f"  [FAIL] FALHA CRITICA (Falso Positivo) em {rule_id}: Esperado={expected_status}, Obtido={actual_status}")
            elif actual_status == expected_status:
                passed_checks += 1
                print(f"  [PASS] {rule_id}: Sucesso (Status: {actual_status})")
            else:
                print(f"  [WARN] {rule_id}: Divergencia. Esperado={expected_status}, Obtido={actual_status}")

    elapsed = time.time() - start_time
    accuracy = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

    print("\n" + "=" * 70)
    print("RESULTADO CONSOLIDADO DO BENCHMARK DE HARNESS EVALS")
    print(f"Total de Verificacoes: {total_checks}")
    print(f"Casos Bem-Sucedidos:   {passed_checks}")
    print(f"Falsos Positivos:      {false_positives} (Tolerancia Maxima: 0)")
    print(f"Acuracia Geral:        {accuracy:.2f}% (Minimo: {ACCURACY_THRESHOLD:.0f}%)")
    print(f"Tempo de Execucao:     {elapsed:.4f}s")
    print("=" * 70)

    if false_positives > 0 or accuracy < ACCURACY_THRESHOLD:
        print("[FAIL] Regressao detectada nos Evals. O pipeline nao atingiu os criterios de aceitacao.")
        return False

    print("[PASS] Todos os criterios de Evals foram aprovados sem regressoes.")
    return True


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)

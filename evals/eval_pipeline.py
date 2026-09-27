"""Regression and Evaluation Pipeline for Document Extraction & Compliance Rules."""

import os
import sys
import time
from typing import List, Dict, Any

# Garante suporte a UTF-8 no console do Windows/Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Adiciona o backend ao path para importação dos módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.rules_engine import RulesEngine


# Casos de teste de referência com Ground Truth
BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "id": "CASE-001",
        "description": "CND Federal - Certidão Limpa e Regular",
        "input_text": (
            "REPÚBLICA FEDERATIVA DO BRASIL - MINISTÉRIO DA FAZENDA\n"
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "É certificado que não constam pendências em nome do sujeito passivo."
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
        "description": "CRF FGTS Regular",
        "input_text": (
            "CAIXA ECONÔMICA FEDERAL\n"
            "CERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
            "Inscrição: 12.345.678/0001-90\n"
            "A Caixa Econômica Federal certifica que a empresa encontra-se em SITUAÇÃO REGULAR."
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
    }
]



def run_evaluation() -> bool:
    print("=" * 70)
    print("Conform.IA BNDES - Pipeline de Avaliacao Continua (Evals)")
    print("=" * 70)

    engine = RulesEngine(rules_file="rules/schemas/bndes_sample_checklist.json")
    total_checks = 0
    passed_checks = 0
    false_positives = 0
    start_time = time.time()

    for case in BENCHMARK_CASES:
        print(f"\n[EVAL] Executando {case['id']}: {case['description']}")
        eval_result = engine.evaluate({"full_text": case["input_text"], "metadata": {}})
        
        # Mapeia resultados por rule_id
        actual_by_rule = {r["rule_id"]: r["status"] for r in eval_result["results"]}

        for rule_id, expected_status in case["expected_results"].items():
            total_checks += 1
            actual_status = actual_by_rule.get(rule_id, "NOT_EVALUATED")

            # Verificacao estrita de Falso Positivo (rejeitar algo irregular dado como conforme)
            if expected_status == "NON_COMPLIANT" and actual_status == "COMPLIANT":
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
    print(f"Acuracia Geral:        {accuracy:.2f}%")
    print(f"Tempo de Execucao:     {elapsed:.4f}s")
    print("=" * 70)

    if false_positives > 0 or accuracy < 90.0:
        print("[FAIL] Regressao detectada nos Evals. O pipeline nao atingiu os criterios de aceitacao.")
        return False

    print("[PASS] Todos os criterios de Evals foram aprovados sem regressoes.")
    return True


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)

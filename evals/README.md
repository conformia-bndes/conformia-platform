# Framework de Avaliação Contínua (Evals) - Conform.IA BNDES

Este diretório contém os componentes de Evals (Avaliação Contínua) para o pipeline de Processamento Inteligente de Documentos (IDP) e o motor de conformidade regulatória do BNDES (Consulta Pública nº 01/2025).

---

## Objetivos de Harness e Métricas Chave

Em sistemas críticos de conformidade de crédito público, alucinações ou falsos negativos em certidões são inaceitáveis. O framework de Evals mensura e protege contra regressões através das seguintes métricas:

| Métrica | Meta Mínima | Descrição |
| :--- | :--- | :--- |
| **Extraction Recall (Entidades)** | $\ge 98.5\%$ | Percentual de dados obrigatórios (CNPJ, datas de validade, códigos de controle) extraídos corretamente. |
| **CER (Character Error Rate)** | $\le 1.5\%$ | Taxa de erro de caracteres no OCR em documentos digitalizados (scanned). |
| **Falsos Positivos de Conformidade** | **$0.0\%$** (Zero Tolerância) | Nunca classificar como `COMPLIANT` uma certidão com pendências ou débitos ativos. |
| **Maker-Checker Agreement Rate** | $\ge 95.0\%$ | Taxa de concordância entre a hipótese do agente Maker e a crítica do agente Checker. |
| **Hallucination Detection Rate** | $\ge 99.0\%$ | Capacidade do Checker de interceptar e invalidar asserções que não constem no texto original. |

---

## Estrutura de Testes de Regressão

```text
evals/
├── README.md               # Este guia com diretrizes e metas
├── eval_pipeline.py        # Script automatizado de benchmark de regressao
└── datasets/               # Casos de teste sinteticos e reais anonimizados
    ├── compliant/          # Documentos com conformidade 100% atestada
    ├── non_compliant/      # Documentos com debitos, fraudes ou irregularidades
    └── edge_cases/         # Documentos com carimbos ilegiveis, baixa resolucao e rotacao
```

---

## Execução dos Evals

Para rodar a bateria de testes de avaliação de regressão:

```bash
# A partir da raiz do monorepo:
python evals/eval_pipeline.py

# Ou via Makefile:
make eval
```

O script reportara a matriz de confusao, acurácia por regra do checklist BNDES e tempo médio de inferência por página.

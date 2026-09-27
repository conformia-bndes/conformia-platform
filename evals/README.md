# Framework de Avaliacao Continua (Evals) - Conform.IA BNDES

Este diretorio contem os componentes de Evals (Avaliacao Continua) para o pipeline de Processamento Inteligente de Documentos (IDP) e o motor de conformidade regulatoria do BNDES (Consulta Publica no 01/2025).

---

## Objetivos de Harness e Metricas Chave

Em sistemas criticos de conformidade de credito publico, alucinacoes ou falsos negativos em certidoes sao inaceitaveis. O framework de Evals mensura e protege contra regressoes atraves das seguintes metricas:

| Metrica | Meta Minima | Descricao |
| :--- | :--- | :--- |
| **Extraction Recall (Entidades)** | $\ge 98.5\%$ | Percentual de dados obrigatorios (CNPJ, datas de validade, codigos de controle) extraidos corretamente. |
| **CER (Character Error Rate)** | $\le 1.5\%$ | Taxa de erro de caracteres no OCR em documentos digitalizados (scanned). |
| **Falsos Positivos de Conformidade** | **$0.0\%$** (Zero Tolerancia) | Nunca classificar como `COMPLIANT` uma certidao com pendencias ou debitos ativos. |
| **Maker-Checker Agreement Rate** | $\ge 95.0\%$ | Taxa de concordancia entre a hipotese do agente Maker e a critica do agente Checker. |
| **Hallucination Detection Rate** | $\ge 99.0\%$ | Capacidade do Checker de interceptar e invalidar assercoes que nao constem no texto original. |

---

## Estrutura de Testes de Regressao

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

## Execucao dos Evals

Para rodar a bateria de testes de avaliacao de regressao:

```bash
# A partir da raiz do monorepo:
python evals/eval_pipeline.py

# Ou via Makefile:
make eval
```

O script reportara a matriz de confusao, acuracia por regra do checklist BNDES e tempo medio de inferencia por pagina.

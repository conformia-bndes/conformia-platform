# MLOps: Avaliação, Rastreio e Governança de IA

O Conform.IA combina regras determinísticas, OCR e um LLM no padrão Maker-Checker. Esta página
define como medir, versionar e liberar mudanças nesses componentes sem perder a garantia
central do produto: **nenhuma certidão irregular é aprovada**.

!!! abstract "Princípio fail-closed"
    Falha do LLM, resposta malformada, citação que não existe no documento ou falta de data de
    validade resultam em `MANUAL_REVIEW_REQUIRED`. Nunca em `COMPLIANT`.

---

## 1. O que é versionado

| Artefato | Onde | Versionamento |
| :-- | :-- | :-- |
| Regras e checklist | `rules/schemas/` | Git; o hash SHA-256 do checklist entra em cada relatório de evals |
| Casos de referência (texto) | `evals/eval_pipeline.py` e `evals/datasets/` | Git, com ground truth junto do caso |
| Dataset sintético de PDFs | `evals/sintetico/` | Gerado de forma determinística por `gerar_dataset.py`; gabarito em Git |
| Prompts do Maker e do Checker | `backend/app/ai/llm_client.py` | Git; mudanças exigem `make llm-eval` |
| Modelo LLM | `LLM_MODEL` no `.env` | Registrado como parâmetro em cada execução |
| Resultados de avaliação | Artefato `eval-report` do CI e MLflow local | Retenção de 30 dias no CI |

---

## 2. Camadas de avaliação

| Camada | Comando | Mede | Bloqueia merge? |
| :-- | :-- | :-- | :-- |
| Regras determinísticas | `make eval` | Status por regra no caminho do produto (parser + tipologia) | Sim: 0 falsos positivos e acurácia mínima de 90% |
| Extração e OCR (sintético) | `uv run python evals/sintetico/avaliar.py` | Tipo, CNPJ, validade e pendência por PDF | Não (linha de base) |
| Comportamento do LLM | `make llm-eval` | Maker-Checker contra alucinação e injeção de instruções | Não; manual, exige `OPENAI_API_KEY` |
| Testes unitários do harness | `pytest backend/tests/test_maker_checker.py` | Fail-closed sem rede, com cliente simulado | Sim |

!!! warning "Limites estatísticos"
    Os conjuntos atuais são pequenos e sintéticos. Servem para detectar regressões, não para
    estimar a qualidade em produção. Metas de precisão e recall só devem ser definidas após a
    inclusão de PDFs reais anonimizados (issue de evals com documentos reais).

**Falso positivo** é qualquer `COMPLIANT` cuja verdade não é `COMPLIANT`, inclusive quando o
esperado era revisão manual.

---

## 3. Rastreio de experimentos (MLflow)

Cada execução dos evals pode ser registrada no MLflow sem adicioná-lo às dependências do projeto:

```bash
make eval-mlflow
# equivale a:
uv run --with mlflow==3.17.2 python evals/eval_pipeline.py --mlflow \
  --json-report evals/reports/eval_report.json
```

| Registrado | Conteúdo |
| :-- | :-- |
| Parâmetros | commit, hash do checklist, data de referência, limiar de acurácia |
| Métricas | `total_checks`, `passed_checks`, `false_positives`, `accuracy` |
| Artefato | Relatório JSON com o resultado de cada verificação |

O armazenamento padrão é o SQLite local `mlflow.db` (ignorado pelo Git). Para comparar
execuções: `uv run --with mlflow==3.17.2 mlflow ui --backend-store-uri sqlite:///mlflow.db`.
Para um servidor compartilhado, defina `MLFLOW_TRACKING_URI`.

---

## 4. Governança do LLM

1. **Contexto delimitado:** o Maker recebe apenas a regra e até 3.000 caracteres do documento.
2. **Citação obrigatória:** a aprovação exige que o trecho citado pelo Maker exista literalmente
   no documento (ignorando acentos, caixa e espaços).
3. **Checker independente:** precisa aprovar e declarar `hallucination_detected: false`.
4. **Domínio fechado:** avaliações fora de `COMPLIANT`, `NON_COMPLIANT` e
   `MANUAL_REVIEW_REQUIRED` são rejeitadas.
5. **Sem dados pessoais em logs:** falhas do provedor registram apenas o tipo da exceção.
6. **Mudança de prompt ou modelo:** abrir PR com o resultado de `make llm-eval` anexado.

---

## 5. Ciclo de mudança em componentes de IA

```text
issue -> branch -> alteração (regra, prompt, modelo ou parser)
      -> make eval  (0 falsos positivos)          -> bloqueante no CI
      -> make llm-eval (se prompt/modelo mudou)   -> resultado anexado ao PR
      -> make eval-mlflow (comparação com a execução anterior)
      -> revisão do time ai-evals (CODEOWNERS)
      -> merge em dev
```

---

## 6. Monitoramento em produção (planejado)

Ainda não implementado. Itens propostos para depois do MVP:

- Taxa de `MANUAL_REVIEW_REQUIRED` por tipologia e por semana (sinal de deriva de OCR ou de layout).
- Taxa de divergência entre o laudo automatizado e a decisão humana (`review_events`).
- Latência e custo por chamada ao LLM.
- Alertas quando a taxa de revisão manual mudar mais de um limiar acordado com o negócio.

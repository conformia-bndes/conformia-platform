# Avaliação Contínua (Evals)

Os evals medem se o produto toma a decisão certa e impedem regressões. São três suítes, com
papéis diferentes:

| Suíte | Comando | O que mede | Bloqueia o CI? |
| :-- | :-- | :-- | :-- |
| Benchmark de regras | `make eval` | Status por regra no caminho do produto (parser, tipologia e motor) | Sim |
| Dataset sintético de PDFs | `uv run python evals/sintetico/avaliar.py` | Extração, OCR e classificação de 22 certidões fictícias | Não (linha de base) |
| Comportamento do LLM | `make llm-eval` | Maker-Checker contra alucinação e injeção de instruções (promptfoo) | Não; manual e pago |
| Fuzzing | Job "Fuzzing do motor de regras" do CI | Invariantes de segurança com textos arbitrários (Atheris) | Sim |

O versionamento dos resultados e a comparação entre execuções estão em [MLOps](mlops.md).

---

## 1. Benchmark de regras (`evals/eval_pipeline.py`)

Executa os casos de `evals/datasets/` (conformes, não conformes e casos de borda) pelo mesmo
caminho do produto e compara o status de cada verificação com o esperado.

**Critério de aprovação:** zero falsos positivos (nenhum `COMPLIANT` indevido) e acurácia
mínima de 90%. O job de backend do CI falha se qualquer um dos dois não for atendido e publica
o relatório JSON (`--json-report`) como artefato.

**Última execução local (29/10/2026):** 14 verificações, 13 corretas, **0 falsos positivos**,
acurácia de 92,86%. A divergência restante é conservadora: uma certidão ilegível esperada como
`MANUAL_REVIEW_REQUIRED` saiu `NON_COMPLIANT`.

!!! note "Alcance"
    O benchmark tem poucos casos e todos são sintéticos. Ele protege contra regressões nas
    regras, mas não mede o desempenho com documentos reais.

---

## 2. Dataset sintético de PDFs (`evals/sintetico/`)

22 certidões fictícias (CND federal e CRF do FGTS), 12 nativas e 10 digitalizadas, cobrindo
documentos válidos, vencidos, com pendência, ilegíveis e sem validade. O gabarito traz a
evidência esperada e a página de cada campo. A metodologia completa está em
`evals/sintetico/RELATORIO.md`.

A linha de base registrada em 19/10/2026 (anterior à correção da validade obrigatória) teve
extração de 82/82 trechos de evidência e classificação correta em 10 de 22 documentos, com 6
falsos positivos. As correções posteriores (validade obrigatória para FISCAL e TRABALHISTA e
filtro por tipologia) atacam essas falhas; a medição atualizada depende de uma nova execução com
Tesseract instalado.

---

## 3. Comportamento do LLM (`evals/promptfoo/`)

Testa o Maker-Checker com o modelo real: aprovação só com citação existente, rejeição de
documentos com pendência e resistência a instruções injetadas no texto do PDF. Roda manualmente
(`make llm-eval` ou workflow `llm-evals.yml`) porque consome créditos e exige `OPENAI_API_KEY`.
Toda mudança de prompt ou de modelo deve anexar o resultado ao PR.

---

## 4. Fuzzing (`backend/fuzz/`)

O `fuzz_regras.py` usa o Atheris (libFuzzer para Python) para gerar textos arbitrários de
documento por 60 segundos em cada PR que altera o backend. Em vez de procurar só exceções, ele
verifica as invariantes de segurança:

1. Nenhum texto derruba a extração de validade, o motor de regras ou a verificação de citação.
2. Com o LLM indisponível, nenhuma regra avaliada pelo Maker-Checker sai `COMPLIANT`.
3. Certidão fiscal ou trabalhista só sai `COMPLIANT` com data de validade identificada.
4. O laudo geral só é `COMPLIANT` quando todas as regras aplicáveis são `COMPLIANT`.
5. Todo trecho literal do documento é aceito como citação, e toda citação aceita existe no texto.

O Atheris só publica pacotes para Linux com Python 3.12+, por isso fica no extra `fuzz` do
backend e roda no CI. As invariantes ficam na função `check()`, que pode ser chamada sem o
Atheris em qualquer sistema.

---

## 4. Metas ainda não medidas

As métricas abaixo orientam a evolução, mas **ainda não são calculadas** por nenhuma suíte:

| Dimensão | Indicador | Meta |
| :-- | :-- | :-- |
| Qualidade do OCR | Character Error Rate (CER) | ≤ 1,5% |
| Extração | Recall de entidades (CNPJ, datas) | ≥ 98,5% |
| IA | Concordância Maker-Checker | ≥ 95% |

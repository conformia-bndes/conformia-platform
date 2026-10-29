# Relatorio de Validacao

Ambiente: Windows 11, Git Bash, `uv 0.11.18`, Python do venv 3.13.13 (CI usa 3.11), Node 24.20.0,
npm 11.19.0. Docker 29.8.2 instalado, **daemon parado**. Tesseract **nao instalado**.
Base: branch `developer`, commit `d76f41c`, working tree limpa no inicio.

Os comandos foram executados na raiz do repositorio com `PYTHONIOENCODING=utf-8`.

---

## 1. Linha de base (antes das alteracoes)

| Verificacao | Comando | Resultado |
| :-- | :-- | :-- |
| Lockfile | `uv lock --check` | OK (109 pacotes resolvidos) |
| Sync | `uv sync --all-packages --all-extras --frozen` | OK |
| Testes backend | `uv run --frozen pytest backend/tests/ -q --cov=backend/app` | 46 passed, 1 skipped (OCR: Tesseract ausente). Cobertura 81%; `celery_app.py` 13% |
| Formatacao | `uv run --frozen black --check backend/` | OK (47 arquivos) |
| Lint | `uv run --frozen flake8 backend/ --count` | 0 |
| Evals | `uv run --frozen python evals/eval_pipeline.py` | 5/5, 0 falsos positivos. **Porem** CASE-001 e CASE-003 esperavam COMPLIANT sem data de validade (contrario ao AGENTS.md) |
| Migrations | `alembic upgrade head` + `alembic check` em SQLite descartavel (`$TEMP/conformia_repro/alembic_check.db`) | "No new upgrade operations detected" |
| Frontend lint | `npm run lint` | OK |
| Frontend testes | `npm test` | 2 passed |
| Frontend build | `npm run build` | OK (296 kB JS) |
| Compose / smoke | `make up && make smoke` | **Nao executado**: daemon Docker indisponivel |
| OCR real | `test_scanned_pdf_triggers_ocr_fallback` | **Nao executado** (skip): Tesseract ausente |
| Gitleaks / pip-audit | - | **Nao executado**: ferramentas nao instaladas localmente (rodam no job `security` do CI) |

### Defeitos reproduzidos antes da correcao

Script descartavel fora do repositorio (`$TEMP/conformia_repro/repro.py`), sem chave de LLM:

```text
D3 clean CND overall: NON_COMPLIANT {'RULE-BNDES-001': 'COMPLIANT', 'RULE-BNDES-002': 'NON_COMPLIANT',
   'RULE-BNDES-003': 'NON_COMPLIANT', 'RULE-BNDES-004': 'NON_COMPLIANT', 'RULE-BNDES-005': 'NON_COMPLIANT',
   'RULE-BNDES-006': 'NON_COMPLIANT'}
```

- CND valida reprovada por regras de outras tipologias (T04b).
- CND sem data de validade: COMPLIANT (teste `test_rules_engine_deterministic_compliant` exigia isso) (T04a).
- Frontend: leitura do codigo de `App.tsx` mostrou laudo "100% Conforme" e upload "COMPLETED"
  fabricados em qualquer erro da API (T06a).
- `LLMClient._mock_response` retornava avaliacao e citacao fixas; na pratica o ciclo acabava
  em revisao manual por acaso (a palavra "maker" nao aparecia no prompt do Maker), mas a
  evidencia fabricada era gravada no laudo (T03b).

---

## 2. Apos as alteracoes

| Verificacao | Comando | Resultado |
| :-- | :-- | :-- |
| Testes backend | `uv run --frozen pytest backend/tests/ -q --cov=backend/app` | **71 passed, 1 skipped** (OCR), codigo 0. Cobertura 86% (`celery_app.py` 13% -> 70%, `compliance_service.py` 100%, `llm_client.py` 95%). Duracao ~5 min por timeouts de rede preexistentes (T11) |
| Formatacao | `uv run --frozen black --check backend/` | OK (48 arquivos) |
| Lint | `uv run --frozen flake8 backend/ --count` | 0 |
| Evals | `uv run --frozen python evals/eval_pipeline.py` | **PASS**: 14 verificacoes, 13 corretas, **0 falsos positivos**, 92,86% (minimo 90%). Divergencia unica: `DATASET-EDGECASE-001` esperado MANUAL_REVIEW_REQUIRED, obtido NON_COMPLIANT (decisao D2) |
| Frontend lint | `npm run lint` | OK |
| Frontend testes | `npm test` | 8 passed (2 arquivos) |
| Frontend build | `npm run build` (inclui `tsc`) | OK (295 kB JS) |
| Docs | `uv run --frozen mkdocs build --strict` | OK apos o commit das paginas novas (antes do commit falhava apenas por avisos do plugin `git-revision-date` em arquivos sem historico git) |
| Compose / smoke | `make up && make smoke` | **Nao executado** (Docker parado) |

### Reproducao apos a correcao (`$TEMP/conformia_repro/repro_after.py`)

```text
D3 clean CND overall: CND_FEDERAL COMPLIANT {'RULE-BNDES-001': 'COMPLIANT', 'RULE-BNDES-002': 'NOT_APPLICABLE', ...}
D1 CND without validity: MANUAL_REVIEW_REQUIRED
D2 hybrid without LLM key: MANUAL_REVIEW_REQUIRED LLM_UNAVAILABLE maker_output= None
```

### Testes alterados (e por que nao e enfraquecimento)

- `test_rules_engine_deterministic_compliant` e `test_rules_engine_category_filtering`: as
  entradas ganharam `Valida ate: 31/12/2099`. A assercao continua `COMPLIANT`; antes ela so
  passava porque o motor aprovava certidoes sem validade. O caso sem validade virou teste
  proprio exigindo `MANUAL_REVIEW_REQUIRED`.
- Evals CASE-001 e CASE-003: mesma correcao de ground truth; casos sem validade viraram
  CASE-006 e CASE-007 com expectativa de revisao manual.
- `test_maker_checker_fallback` foi substituido por 13 testes que exigem revisao manual sem
  saida fabricada.

---

## 3. Limitacoes desta validacao

1. Nenhum teste com Postgres, Redis, MinIO e worker reais. O worker foi exercitado chamando a
   tarefa diretamente com SQLite em memoria; o despacho pela fila nao foi testado.
2. OCR nao testado (Tesseract ausente). A imagem Docker instala `tesseract-ocr-por`.
3. Integracao LLM real nao testada (sem chave). Apenas os caminhos de falha e um cliente
   falso com respostas roteirizadas.
4. Evals usam textos sinteticos; o resultado nao e evidencia estatistica de qualidade.
5. Venv local usa Python 3.13; o CI e a imagem usam 3.11 (diferenca nao testada aqui).
6. Seguranca: revisao manual de codigo (autenticacao, upload, segredos em logs, saida de
   erros). Sem SAST, sem gitleaks e sem pip-audit nesta maquina. Nenhuma conformidade com
   OWASP/NIST e declarada.

# Relatório de Validação

Ambiente: Windows 11, Git Bash, `uv 0.11.18`, Python do venv 3.13.13 (CI usa 3.11), Node 24.20.0,
npm 11.19.0. Docker 29.8.2 instalado, **daemon parado**. Tesseract **não instalado**.
Base: branch `developer`, commit `d76f41c`, working tree limpa no início.

Os comandos foram executados na raiz do repositório com `PYTHONIOENCODING=utf-8`.

---

## 1. Linha de base (antes das alterações)

| Verificação | Comando | Resultado |
| :-- | :-- | :-- |
| Lockfile | `uv lock --check` | OK (109 pacotes resolvidos) |
| Sync | `uv sync --all-packages --all-extras --frozen` | OK |
| Testes backend | `uv run --frozen pytest backend/tests/ -q --cov=backend/app` | 46 passed, 1 skipped (OCR: Tesseract ausente). Cobertura 81%; `celery_app.py` 13% |
| Formatação | `uv run --frozen black --check backend/` | OK (47 arquivos) |
| Lint | `uv run --frozen flake8 backend/ --count` | 0 |
| Evals | `uv run --frozen python evals/eval_pipeline.py` | 5/5, 0 falsos positivos. **Porém** CASE-001 e CASE-003 esperavam COMPLIANT sem data de validade (contrário ao AGENTS.md) |
| Migrations | `alembic upgrade head` + `alembic check` em SQLite descartável (`$TEMP/conformia_repro/alembic_check.db`) | "No new upgrade operations detected" |
| Frontend lint | `npm run lint` | OK |
| Frontend testes | `npm test` | 2 passed |
| Frontend build | `npm run build` | OK (296 kB JS) |
| Compose / smoke | `make up && make smoke` | **Não executado**: daemon Docker indisponível |
| OCR real | `test_scanned_pdf_triggers_ocr_fallback` | **Não executado** (skip): Tesseract ausente |
| Gitleaks / pip-audit | - | **Não executado**: ferramentas não instaladas localmente (rodam no job `security` do CI) |

### Defeitos reproduzidos antes da correção

Script descartável fora do repositório (`$TEMP/conformia_repro/repro.py`), sem chave de LLM:

```text
D3 clean CND overall: NON_COMPLIANT {'RULE-BNDES-001': 'COMPLIANT', 'RULE-BNDES-002': 'NON_COMPLIANT',
   'RULE-BNDES-003': 'NON_COMPLIANT', 'RULE-BNDES-004': 'NON_COMPLIANT', 'RULE-BNDES-005': 'NON_COMPLIANT',
   'RULE-BNDES-006': 'NON_COMPLIANT'}
```

- CND valida reprovada por regras de outras tipologias (T04b).
- CND sem data de validade: COMPLIANT (teste `test_rules_engine_deterministic_compliant` exigia isso) (T04a).
- Frontend: leitura do código de `App.tsx` mostrou laudo "100% Conforme" e upload "COMPLETED"
  fabricados em qualquer erro da API (T06a).
- `LLMClient._mock_response` retornava avaliação e citação fixas; na prática o ciclo acabava
  em revisão manual por acaso (a palavra "maker" não aparecia no prompt do Maker), mas a
  evidência fabricada era gravada no laudo (T03b).

---

## 2. Após as alterações

| Verificação | Comando | Resultado |
| :-- | :-- | :-- |
| Testes backend | `uv run --frozen pytest backend/tests/ -q --cov=backend/app` | **71 passed, 1 skipped** (OCR), código 0. Cobertura 86% (`celery_app.py` 13% -> 70%, `compliance_service.py` 100%, `llm_client.py` 95%). Duração ~5 min por timeouts de rede preexistentes (T11) |
| Formatação | `uv run --frozen black --check backend/` | OK (48 arquivos) |
| Lint | `uv run --frozen flake8 backend/ --count` | 0 |
| Evals | `uv run --frozen python evals/eval_pipeline.py` | **PASS**: 14 verificações, 13 corretas, **0 falsos positivos**, 92,86% (mínimo 90%). Divergência única: `DATASET-EDGECASE-001` esperado MANUAL_REVIEW_REQUIRED, obtido NON_COMPLIANT (decisão D2) |
| Frontend lint | `npm run lint` | OK |
| Frontend testes | `npm test` | 8 passed (2 arquivos) |
| Frontend build | `npm run build` (inclui `tsc`) | OK (295 kB JS) |
| Docs | `uv run --frozen mkdocs build --strict` | OK após o commit das páginas novas (antes do commit falhava apenas por avisos do plugin `git-revision-date` em arquivos sem histórico git) |
| Compose / smoke | `make up && make smoke` | **Não executado** (Docker parado) |

### Reprodução após a correção (`$TEMP/conformia_repro/repro_after.py`)

```text
D3 clean CND overall: CND_FEDERAL COMPLIANT {'RULE-BNDES-001': 'COMPLIANT', 'RULE-BNDES-002': 'NOT_APPLICABLE', ...}
D1 CND without validity: MANUAL_REVIEW_REQUIRED
D2 hybrid without LLM key: MANUAL_REVIEW_REQUIRED LLM_UNAVAILABLE maker_output= None
```

### Testes alterados (e por que não e enfraquecimento)

- `test_rules_engine_deterministic_compliant` e `test_rules_engine_category_filtering`: as
  entradas ganharam `Valida ate: 31/12/2099`. A asserção continua `COMPLIANT`; antes ela só
  passava porque o motor aprovava certidões sem validade. O caso sem validade virou teste
  próprio exigindo `MANUAL_REVIEW_REQUIRED`.
- Evals CASE-001 e CASE-003: mesma correção de ground truth; casos sem validade viraram
  CASE-006 e CASE-007 com expectativa de revisão manual.
- `test_maker_checker_fallback` foi substituído por 13 testes que exigem revisão manual sem
  saída fabricada.

---

## 3. Incremento: identidade por chave pessoal e revisão humana (T05a, T05b)

| Verificação | Comando | Resultado |
| :-- | :-- | :-- |
| Testes backend | `uv run --frozen pytest backend/tests/ -q --cov=backend/app` | **94 passed, 1 skipped** (OCR), código 0. Cobertura 89% (`security.py` 100%, `review_service.py` 99%) |
| Testes novos | `pytest backend/tests/test_reviews.py backend/tests/test_config.py` | 26 passed (17 de revisão, 5 novos de configuração) |
| Migration 002 | `alembic upgrade head`, `alembic check`, `alembic downgrade -1`, `alembic upgrade head` em SQLite descartável (`$TEMP/conformia_repro/alembic_check_002.db`) | Upgrade e downgrade OK; "No new upgrade operations detected" |
| Formatação / lint | `black --check backend/`, `flake8 backend/` | OK / 0 |
| Evals | `python evals/eval_pipeline.py` | PASS, 0 falsos positivos (inalterado) |
| Docs | `mkdocs build --strict` | OK |
| Script de chave | `python backend/scripts/create_api_user.py ana.silva ANALISTA` | Gera chave e entrada JSON; argumentos inválidos retornam 2 |

Não validado: migration 002 em PostgreSQL; concorrência real (o lock `with_for_update` e a
restrição única foram verificados apenas por leitura de código e teste sequencial).

---

## 4. Validação de Infraestrutura Conteinerizada, Fila e OCR (T09a / Issue #46)

Execução com Docker ativo e validação contínua nos workflows `ci-infra.yml` e `ci-backend.yml`:

| Verificação | Comando | Resultado |
| :-- | :-- | :-- |
| Subida da stack (`make up`) | `docker compose --env-file .env -f infra/docker-compose.yml up -d --wait` | **OK**: PostgreSQL, Redis, MinIO, `migrate` (Alembic), `backend`, `worker` e `frontend` saudáveis em ~19 s a partir de volumes limpos |
| Teste de fumaça (`make smoke`) | `docker compose --env-file .env -f infra/docker-compose.yml exec -T backend python scripts/smoke_test.py` | **Código 0**: `1/4 health OK` -> `2/4 upload OK` -> `3/4 tarefa concluida pelo worker (SUCCESS)` -> `4/4 documento COMPLETED (paginas: 1)` |
| OCR no container (`tesseract-ocr-por`) | `docker run --rm scan/backend:ci python scripts/validate_ocr_container.py` | **Código 0**: PDF rasterizado (200 DPI, sem camada de texto) extraído via `extraction_method=ocr`, tipologia `CND_FEDERAL` e CNPJ `12.345.678/0001-90` |
| Resiliência de dependências | `bash scripts/resilience_test.sh` | **OK**: queda isolada de Redis, MinIO e PostgreSQL degrada com HTTP `503` sem travar o healthcheck e recupera automaticamente |
| Problemas encontrados e endereçados | Issues `#101` a `#104` | `.env` antigo sem `API_KEY` (`#101`), validação do CD (`#102`), limites de recursos e concorrência (`#103`) e timeout de upload (`#104`) |

### Saída registrada do `make smoke` e validação de OCR no container

```text
[smoke] API: http://localhost:8000
[smoke] 1/4 health OK: {'database': 'healthy', 'redis': 'healthy', 'minio': 'healthy'}
[smoke] 2/4 upload OK: document_id=8f14e45f-ceea-467f-a811-2a3d9c5f0b12 task_id=3c91a7b0-4d12-4e8a-9c01-7e5b6d8a2f41
[smoke]      estado da tarefa: STARTED
[smoke]      estado da tarefa: SUCCESS
[smoke] 3/4 tarefa concluida pelo worker: {'document_id': '8f14e45f-ceea-467f-a811-2a3d9c5f0b12', 'status': 'COMPLETED', 'overall_status': 'MANUAL_REVIEW_REQUIRED', 'compliance_score': 0.0}
[smoke] 4/4 documento COMPLETED (paginas: 1)
[smoke] OK - ambiente sobe e processa pela fila. Estados observados: STARTED -> SUCCESS

[ocr-check] OK - OCR validado com PDF digitalizado: method=ocr type=CND_FEDERAL cnpj=12.345.678/0001-90 validade=2030-12-31
```

---

## 5. Limitações desta validação

1. Integração LLM real não testada no pipeline padrão (sem chave `OPENAI_API_KEY`); exercitada apenas sob demanda via `make llm-eval` e com clientes falsos roteirizados na suíte unitária.
2. Evals padrão usam textos e PDFs sintéticos; resultados medem regressão determinística do motor e do parser, não qualidade estatística sobre acervo real.
3. Segurança verificada no CI via `gitleaks`, `pip-audit`, `CodeQL` e `Trivy` (`HIGH`/`CRITICAL`). Nenhuma certificação formal OWASP/NIST é declarada.

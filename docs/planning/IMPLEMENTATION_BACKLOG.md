# Backlog de Implementação - Entrega 05/12/2026

Atualizado em 21/11/2026 com o estado de **13/11/2026** (branch de integração `dev`, commit
`627a95a`). Versão anterior: auditoria de 29/10/2026 (histórico na seção final).
Prioridades: **P0** impede fluxo essencial, compromete segurança ou a entrega; **P1** necessário
para confiabilidade/demo consistente; **P2** adiável.

Cada item foi confirmado no código antes de entrar aqui. Hipóteses da análise preliminar que
**não** se confirmaram estão na seção final. A coluna "Entrega" aponta o PR (e o commit
principal) que integrou o item em `dev`.

---

## Concluídos

| ID | Prio | Problema (evidência) | Ação | Testes | Entrega |
| :-- | :-- | :-- | :-- | :-- | :-- |
| T04a | P0 | Certidão FISCAL/TRABALHISTA **sem data de validade era COMPLIANT** (`rules_engine.py`: revisão manual só com `strict_validity`, ausente no checklist). Viola AGENTS.md diretriz 1. | Validade obrigatória por padrão nessas categorias; `requires_validity` explícito no checklist e no schema; expiração comparada por data (válida até o fim do dia); relógio injetável. | `test_rules_advanced.py` (ausente, mesmo dia, dia anterior, data impossível) | PR #44 (`bcc3d7f`) |
| T04b | P0 | **Todas as regras aplicadas a todo documento**: uma CND válida saía `NON_COMPLIANT` porque "não era" CRF, CNDT etc. (reproduzido: 1 COMPLIANT + 5 NON_COMPLIANT). | `evaluate(document_type=...)`: só regras com `code` igual à tipologia; demais `NOT_APPLICABLE`; tipologia não identificada -> revisão manual (`not_evaluable`); score ignora `NOT_APPLICABLE` (`summarize_statuses`). | `test_rules_advanced.py`, `test_compliance.py` | PR #44 (`bcc3d7f`) |
| T03a | P0 | Worker e API avaliavam de formas diferentes (chaves `checks`/`results`, auditoria distinta) e o worker **duplicava checagens em retry**. | `services/compliance_service.py::evaluate_and_persist` único; laudo e auditoria no mesmo commit; laudo vigente substituído, histórico na auditoria. | `test_verify_is_idempotent_and_audited_each_time`, `test_worker_task_extracts_evaluates_and_completes` | PR #44 (`7c2e00f`) |
| T03b | P0 | **LLM simulado**: sem chave ou com falha HTTP, `LLMClient` devolvia JSON fixo com "Certidão válida até 31/12/2026", gravado como evidência. | `LLMUnavailableError`; nenhuma resposta simulada; Maker-Checker degrada para revisão manual em indisponibilidade, JSON malformado, avaliação fora do domínio, `hallucination_detected` ausente ou citação inexistente no documento. | `test_maker_checker.py` (13 casos) | PR #44 (`dcd939c`) |
| T06a | P0 | **Frontend fabricava resultados** em qualquer erro da API: laudo "100% Conforme", upload "COMPLETED" mesmo com PDF rejeitado (400), documentos, regras e auditoria fictícios. | Removidos todos os fallbacks; banner de erro com o `detail` do backend; rótulos distintos para Conforme / Não Conforme / Revisão Manual / Não Aplicável; status desconhecido nunca vira conforme. | `presentation.test.ts` | PR #44 (`3c5f0e8`) |
| T04d | P1 | Parser não reconhecia **CND positiva** como CND: documento com débitos caía em "tipologia não identificada". | Detecção de `CERTIDAO POSITIVA` + tributos federais como `CND_FEDERAL` (avaliada e reprovada pela regra). | eval CASE-002 | PR #44 (`bcc3d7f`) |
| T08a | P1 | Harness ignorava `evals/datasets/`; avaliava todas as regras (diferente do produto); falso positivo só contava NON_COMPLIANT->COMPLIANT; casos esperavam COMPLIANT sem data de validade. | Harness segue o caminho do produto (parser + tipologia); carrega datasets; data de referência fixa; falso positivo = qualquer COMPLIANT indevido; casos CASE-006/007/008. | `python evals/eval_pipeline.py` | PR #44 |
| T10a | P1 | Hash do arquivo (RF10) não era registrado; upload não gerava auditoria. | Evento `DOCUMENT_UPLOADED` com SHA-256 na auditoria; `sha256` na resposta do upload. | `test_upload_records_sha256_in_audit_trail` | PR #44 (`863985c`) |
| T01a | P1 | CI disparava em `develop`, branch inexistente. | Filtros dos workflows apontam para `main` e `dev` (branch de integração). | `.github/workflows/ci.yml` (`branches: [main, dev]`) | PR #44 (`1a26927`), PR #65 (`1503c58`) |
| T05a | P0 | Sem identidade de usuário: uma chave única e acesso anônimo em `development`/`test`. | **D1 decidida (29/10): chaves pessoais.** `API_USERS` (JSON com `user_id`, `role` ANALISTA/AUDITOR/ADMIN, `key_hash` PBKDF2-HMAC-SHA256 com sal; chave no formato `user_id:segredo`); comparação em tempo constante; `verify_api_key` aceita chave pessoal e não devolve mais a chave; `require_role` sem acesso anônimo nem chave de serviço; script `create_api_user.py`. | `test_reviews.py`, `test_config.py` | PR #45 (`8fcef81`), PR #68 (`9910502`, PBKDF2) |
| T05b | P0 | RF09 inexistente. | Tabela append-only `review_events` (migration 002) e rotas `/compliance/reviews`: proposta (APPROVE/REJECT/EXCEPTION, justificativa 20-4000), confirmação ou devolução por **outro** analista, `resolves_id` único contra resolução concorrente, laudo `NON_COMPLIANT` só aceito como `EXCEPTION`, auditoria `REVIEW_*` com o autor. | `test_reviews.py` (17 casos), `alembic upgrade/check/downgrade` em SQLite descartável | PR #45 (`6adb60f`) |
| T01b | P1 | Imagem Docker instalava `backend/requirements.txt` (faixas `>=`, inclui pytest/black), e não o lock: build não reprodutível. | `infra/Dockerfile.backend` usa `uv sync --frozen --no-dev --package conformia-backend`. | Job de imagens do CI | PR #72 (`f6530cb`) |
| T10b | P2 | `rules-engine.md` não descrevia filtro por tipologia nem validade obrigatória. | `rules-engine.md` reescrito (seleção por tipologia, `requires_validity`); `api-reference.md` corrigido junto com T05b. | `mkdocs build --strict` | PR #73 (`f1f4cfd`) |
| T03c | P2 | Upload lia o arquivo inteiro em memória antes de checar 50 MB; erros 400/500 ecoavam `str(e)`. | Leitura limitada a `MAX_FILE_SIZE + 1`; mensagens genéricas ao cliente. | Testes de upload (limite e falhas de leitura/gravação) | PR #82 (`844ff48`) |
| T04c | P1 | Dataset `edge_cases/sample_cnd_ilegivel.json` esperava revisão manual; motor retornava `NON_COMPLIANT` (palavra-chave obrigatória ausente). | Política D2: termo obrigatório ausente -> `MANUAL_REVIEW_REQUIRED`. | Teste D2 em `backend/tests/`, evals | PR #92 (`8129aa2`) |
| T05d | P1 | Banco já existente não recebia `review_events` sem `alembic upgrade head`; o compose não executava migrations. | Serviço `migrate` (`python -m app.db.migrate`) antes da API e do worker; `create_all` removido do startup. | Testes de migração em PostgreSQL (issue #50) | PR #109 (`85f54a7`) |
| T05c | P1 | `ENVIRONMENT` padrão `development` e `DEBUG=True`: deploy sem `.env` correto ficava sem autenticação e expunha `str(exc)`. | Padrão seguro (`production`, `DEBUG=False`); acesso anônimo só com opt-in `ALLOW_ANONYMOUS_ACCESS`. | `test_config.py` (issue #52) | PR #110 (`7f660db`) |
| T11 | P1 | Suíte de backend levava ~5 min por timeouts de MinIO/Redis/PostgreSQL reais. | Mocks de MinIO, Redis e PostgreSQL nos testes afetados. | `pytest backend/tests/` | PR #108 (`3e402f5`) |

---

## Abertos (estado em 13/11)

| ID | Prio | Problema / evidência | Ação mínima | Dependência | Esforço | Status em 13/11 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| T06c | P0 | Frontend não envia `X-API-Key` (`frontend/src/services/api.ts`); só funciona com `ALLOW_ANONYMOUS_ACCESS=true`, e a revisão humana exige chave pessoal. | Entrada da chave pessoal na sessão do navegador (memória, sem localStorage) e envio no cabeçalho. | - | 0,5-1 d | Pendente |
| T06b | P0 | UI sem fluxo de revisão humana nem exibição de evidências por página. A API de revisão (T05b) já existe. | Painel de decisão no laudo (propor, confirmar, devolver; estado e histórico); exibir `evidence` e trechos por página. | T06c | 2-3 d | Em andamento: evidências por página na branch `55-exibir-evidencias-por-pagina-no-laudo-rf08` (não integrada); painel de decisão pendente |
| T09a | P0 | Compose + smoke não executados na auditoria de 29/10 (Docker parado). | `make up && make smoke` em máquina da equipe; registrar saída no relatório e validar OCR no container. | Docker | 0,5 d | Parcial: smoke em Compose roda no job `smoke` de `ci-infra.yml` (PR #95). Registro manual com saída e validação de OCR no container (issue #46) na branch `docs/validar-compose-smoke-ocr`, ainda não integrada; ver `VALIDATION_REPORT.md` seção 4 |
| T08b | P2 | Evals usam textos e PDFs sintéticos: não medem OCR real nem LLM. | Adicionar PDFs reais anonimizados por tipologia do MVP. | dados | 1 d | Pendente |
| T07a | P2 | `nginx.conf` sem proxy `/api` nem `client_max_body_size`; compose usa o servidor de dev do Vite. | Só necessário se a demo usar o build de produção. | - | 0,5 d | Adiado |

---

## Hipóteses da análise preliminar não confirmadas (auditoria de 29/10/2026, histórico)

| Hipótese | Resultado da verificação |
| :-- | :-- |
| Migrations divergentes dos modelos | **Não confirmada**: `alembic upgrade head` + `alembic check` em SQLite descartável: "No new upgrade operations detected". Risco real era outro: runtime usava `create_all` (resolvido em T05d). |
| Divergência entre gerenciadores de dependências quebra o build local | Parcial: `uv lock --check` ok e `uv sync --frozen` ok; o problema real era a imagem Docker usar `requirements.txt` sem lock (T01b, resolvido). |
| Ausência de processamento assíncrono | **Não confirmada**: Celery + Redis implementados; worker exercitado em teste direto da tarefa. Despacho pela fila validado depois no smoke do CI (T09a). |
| `App.tsx` concentrado exige refatoração | Não priorizado: o defeito real era a fabricação de dados (T06a). Extraído apenas o módulo testável `presentation.ts`. |
| Upload sem validação | **Não confirmada**: extensão, magic bytes `%PDF` e 50 MB já validados; `uuid` no nome evita path traversal. |

# Backlog de Implementação - Entrega 05/12/2026

Atualizado em 29/10/2026. Prioridades: **P0** impede fluxo essencial, compromete segurança ou a
entrega; **P1** necessário para confiabilidade/demo consistente; **P2** adiável.

Cada item foi confirmado no código antes de entrar aqui. Hipóteses da análise preliminar que
**não** se confirmaram estão na seção final.

---

## Concluidos nesta execução

| ID | Prio | Problema (evidência) | Ação | Testes |
| :-- | :-- | :-- | :-- | :-- |
| T04a | P0 | Certidão FISCAL/TRABALHISTA **sem data de validade era COMPLIANT** (`rules_engine.py`: revisão manual so com `strict_validity`, ausente no checklist). Viola AGENTS.md diretriz 1. | Validade obrigatória por padrão nessas categorias; `requires_validity` explicito no checklist e no schema; expiração comparada por data (valida até o fim do dia); relogio injetável. | `test_rules_advanced.py` (ausente, mesmo dia, dia anterior, data impossível) |
| T04b | P0 | **Todas as regras aplicadas a todo documento**: uma CND valida saia `NON_COMPLIANT` porque "não era" CRF, CNDT etc. (reproduzido: 1 COMPLIANT + 5 NON_COMPLIANT). | `evaluate(document_type=...)`: so regras com `code` igual a tipologia; demais `NOT_APPLICABLE`; tipologia não identificada -> revisão manual (`not_evaluable`); score ignora `NOT_APPLICABLE` (`summarize_statuses`). | `test_rules_advanced.py`, `test_compliance.py` |
| T03a | P0 | Worker e API avaliavam de formas diferentes (chaves `checks`/`results`, auditoria distinta) e o worker **duplicava checagens em retry**. | `services/compliance_service.py::evaluate_and_persist` único; laudo e auditoria no mesmo commit; laudo vigente substituido, histórico na auditoria. | `test_verify_is_idempotent_and_audited_each_time`, `test_worker_task_extracts_evaluates_and_completes` |
| T03b | P0 | **LLM simulado**: sem chave ou com falha HTTP, `LLMClient` devolvia JSON fixo com "Certidão valida até 31/12/2026", gravado como evidência. | `LLMUnavailableError`; nenhuma resposta simulada; Maker-Checker degrada para revisão manual em indisponibilidade, JSON malformado, avaliação fora do dominio, `hallucination_detected` ausente ou citação inexistente no documento. | `test_maker_checker.py` (13 casos) |
| T06a | P0 | **Frontend fabricava resultados** em qualquer erro da API: laudo "100% Conforme", upload "COMPLETED" mesmo com PDF rejeitado (400), documentos, regras e auditoria ficticios. | Removidos todos os fallbacks; banner de erro com o `detail` do backend; rotulos distintos para Conforme / Não Conforme / Revisão Manual / Não Aplicável; status desconhecido nunca vira conforme. | `presentation.test.ts` |
| T04d | P1 | Parser não reconhecia **CND positiva** como CND: documento com débitos caia em "tipologia não identificada". | Detecção de `CERTIDAO POSITIVA` + tributos federais como `CND_FEDERAL` (avaliada e reprovada pela regra). | eval CASE-002 |
| T08a | P1 | Harness ignorava `evals/datasets/`; avaliava todas as regras (diferente do produto); falso positivo so contava NON_COMPLIANT->COMPLIANT; casos esperavam COMPLIANT sem data de validade. | Harness segue o caminho do produto (parser + tipologia); carrega datasets; data de referência fixa; falso positivo = qualquer COMPLIANT indevido; casos CASE-006/007/008. | `python evals/eval_pipeline.py` |
| T10a | P1 | Hash do arquivo (RF10) não era registrado; upload não gerava auditoria. | Evento `DOCUMENT_UPLOADED` com SHA-256 na auditoria; `sha256` na resposta do upload. | `test_upload_records_sha256_in_audit_trail` |
| T01a | P1 | CI dispara em `develop`, branch inexistente; a integração usa `developer`. | Filtros do `ci.yml` apontam para `main` e `developer`. | Verificado com `git ls-remote` (sem execução remota) |
| T05a | P0 | Sem identidade de usuário: uma chave unica e acesso anonimo em `development`/`test`. | **D1 decidida (29/10): chaves pessoais.** `API_USERS` (JSON com `user_id`, `role` ANALISTA/AUDITOR/ADMIN, `key_hash` PBKDF2-HMAC-SHA256 com sal; chave no formato `user_id:segredo`); comparação em tempo constante; `verify_api_key` aceita chave pessoal e não devolve mais a chave; `require_role` sem acesso anonimo nem chave de serviço; script `create_api_user.py`. | `test_reviews.py`, `test_config.py` |
| T05b | P0 | RF09 inexistente. | Tabela append-only `review_events` (migration 002) e rotas `/compliance/reviews`: proposta (APPROVE/REJECT/EXCEPTION, justificativa 20-4000), confirmação ou devolução por **outro** analista, `resolves_id` único contra resolução concorrente, laudo `NON_COMPLIANT` so aceito como `EXCEPTION`, auditoria `REVIEW_*` com o autor. | `test_reviews.py` (17 casos), `alembic upgrade/check/downgrade` em SQLite descartável |

---

## Abertos

| ID | Prio | Problema / evidência | Ação mínima | Dependência | Esforço | Status |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| T06b | P0 | UI sem fluxo de revisão humana nem exibição de evidências por página. A API de revisão (T05b) já existe. | Painel de decisão no laudo (propor, confirmar, devolver; estado e histórico); exibir `evidence` e trechos por página. | T06c | 2-3 d | Pendente |
| T05d | P1 | `create_all` no startup cria `review_events` em bancos novos, mas um banco já existente so recebe a tabela via `alembic upgrade head`; o compose não executa migrations. | Executar `alembic upgrade head` na inicialização do backend (ou documentar `make migrate`) e validar em PostgreSQL. | T09a | 0,5 d | Pendente |
| T09a | P0 | Compose + smoke não executados nesta auditoria (Docker parado). | `make up && make smoke` em maquina da equipe; registrar saida no relatório. | Docker | 0,5 d | Pendente |
| T04c | P1 | Dataset `edge_cases/sample_cnd_ilegivel.json` espera revisão manual; motor retorna `NON_COMPLIANT` (palavra-chave obrigatória ausente). Unica divergência restante nos evals. | Aplicar a política decidida em D2. | D2 | 0,5 d | Bloqueado (D2) |
| T01b | P1 | Imagem Docker instala `backend/requirements.txt` (faixas `>=`, inclui pytest/black) e não `requirements.lock`/`uv.lock`: build não reprodutível e diferente do dev/CI. | Instalar a partir de `requirements.lock` (exportado por `make uv-lock`) sem dependências de dev. | - | 0,5 d | Pendente |
| T05c | P1 | `ENVIRONMENT` padrão e `development` e `DEBUG=True`: deploy sem `.env` correto fica sem autenticação e expoe `str(exc)` em erro 500. | Padrão seguro (`production`, `DEBUG=False`) e bypass so com opt-in explicito. | T05a | 0,5 d | Pendente |
| T06c | P0 | Frontend não envia `X-API-Key`; so funciona porque `development` libera acesso anonimo, e a revisão humana exige chave pessoal. | Entrada da chave pessoal na sessão do navegador (memória, sem localStorage) e envio no cabecalho. | - | 0,5-1 d | Pendente |
| T11 | P1 | Suite de backend leva ~5 min: `test_health_endpoint` e 2 testes de upload esperam ~60 s cada por timeout de MinIO/Redis reais; cada TestClient espera ~4 s pelo Postgres no `lifespan`. | Mockar storage/redis nesses testes; tornar `create_all` do lifespan configurável. | - | 0,5 d | Pendente |
| T03c | P2 | Upload le o arquivo inteiro em memória antes de checar 50 MB; erros 400/500 ecoam `str(e)`. | Leitura limitada (`MAX_FILE_SIZE + 1`); mensagens genéricas ao cliente. | - | 0,5 d | Pendente |
| T07a | P2 | `nginx.conf` sem proxy `/api` nem `client_max_body_size`; compose usa o servidor de dev do Vite. | So necessário se a demo usar o build de produção. | - | 0,5 d | Adiado |
| T08b | P2 | Evals usam textos sintéticos (3 PDFs, 11 casos): não medem OCR nem LLM. | Adicionar PDFs reais anonimizados por tipologia do MVP. | dados | 1 d | Pendente |
| T10b | P2 | `rules-engine.md` não descreve filtro por tipologia nem validade obrigatória. (`api-reference.md` corrigido junto com T05b: contrato real do `verify` e rotas de revisão.) | Atualizar `rules-engine.md`. | - | 0,25 d | Parcial |

---

## Hipóteses da análise preliminar não confirmadas

| Hipótese | Resultado da verificação |
| :-- | :-- |
| Migrations divergentes dos modelos | **Não confirmada**: `alembic upgrade head` + `alembic check` em SQLite descartável: "No new upgrade operations detected". Risco real e outro: runtime usa `create_all`. |
| Divergência entre gerenciadores de dependências quebra o build local | Parcial: `uv lock --check` ok e `uv sync --frozen` ok; o problema real e a imagem Docker usar `requirements.txt` sem lock (T01b). |
| Ausência de processamento assincrono | **Não confirmada**: Celery + Redis implementados; worker exercitado em teste direto da tarefa. Não foi validado com broker real. |
| `App.tsx` concentrado exige refatoração | Não priorizado: o defeito real era a fabricação de dados (T06a). Extraido apenas o módulo testável `presentation.ts`. |
| Upload sem validação | **Não confirmada**: extensão, magic bytes `%PDF` e 50 MB já validados; `uuid` no nome evita path traversal. |

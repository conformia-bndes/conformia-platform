# Backlog de Implementacao - Entrega 05/12/2026

Atualizado em 29/10/2026. Prioridades: **P0** impede fluxo essencial, compromete seguranca ou a
entrega; **P1** necessario para confiabilidade/demo consistente; **P2** adiavel.

Cada item foi confirmado no codigo antes de entrar aqui. Hipoteses da analise preliminar que
**nao** se confirmaram estao na secao final.

---

## Concluidos nesta execucao

| ID | Prio | Problema (evidencia) | Acao | Testes |
| :-- | :-- | :-- | :-- | :-- |
| T04a | P0 | Certidao FISCAL/TRABALHISTA **sem data de validade era COMPLIANT** (`rules_engine.py`: revisao manual so com `strict_validity`, ausente no checklist). Viola AGENTS.md diretriz 1. | Validade obrigatoria por padrao nessas categorias; `requires_validity` explicito no checklist e no schema; expiracao comparada por data (valida ate o fim do dia); relogio injetavel. | `test_rules_advanced.py` (ausente, mesmo dia, dia anterior, data impossivel) |
| T04b | P0 | **Todas as regras aplicadas a todo documento**: uma CND valida saia `NON_COMPLIANT` porque "nao era" CRF, CNDT etc. (reproduzido: 1 COMPLIANT + 5 NON_COMPLIANT). | `evaluate(document_type=...)`: so regras com `code` igual a tipologia; demais `NOT_APPLICABLE`; tipologia nao identificada -> revisao manual (`not_evaluable`); score ignora `NOT_APPLICABLE` (`summarize_statuses`). | `test_rules_advanced.py`, `test_compliance.py` |
| T03a | P0 | Worker e API avaliavam de formas diferentes (chaves `checks`/`results`, auditoria distinta) e o worker **duplicava checagens em retry**. | `services/compliance_service.py::evaluate_and_persist` unico; laudo e auditoria no mesmo commit; laudo vigente substituido, historico na auditoria. | `test_verify_is_idempotent_and_audited_each_time`, `test_worker_task_extracts_evaluates_and_completes` |
| T03b | P0 | **LLM simulado**: sem chave ou com falha HTTP, `LLMClient` devolvia JSON fixo com "Certidao valida ate 31/12/2026", gravado como evidencia. | `LLMUnavailableError`; nenhuma resposta simulada; Maker-Checker degrada para revisao manual em indisponibilidade, JSON malformado, avaliacao fora do dominio, `hallucination_detected` ausente ou citacao inexistente no documento. | `test_maker_checker.py` (13 casos) |
| T06a | P0 | **Frontend fabricava resultados** em qualquer erro da API: laudo "100% Conforme", upload "COMPLETED" mesmo com PDF rejeitado (400), documentos, regras e auditoria ficticios. | Removidos todos os fallbacks; banner de erro com o `detail` do backend; rotulos distintos para Conforme / Nao Conforme / Revisao Manual / Nao Aplicavel; status desconhecido nunca vira conforme. | `presentation.test.ts` |
| T04d | P1 | Parser nao reconhecia **CND positiva** como CND: documento com debitos caia em "tipologia nao identificada". | Deteccao de `CERTIDAO POSITIVA` + tributos federais como `CND_FEDERAL` (avaliada e reprovada pela regra). | eval CASE-002 |
| T08a | P1 | Harness ignorava `evals/datasets/`; avaliava todas as regras (diferente do produto); falso positivo so contava NON_COMPLIANT->COMPLIANT; casos esperavam COMPLIANT sem data de validade. | Harness segue o caminho do produto (parser + tipologia); carrega datasets; data de referencia fixa; falso positivo = qualquer COMPLIANT indevido; casos CASE-006/007/008. | `python evals/eval_pipeline.py` |
| T10a | P1 | Hash do arquivo (RF10) nao era registrado; upload nao gerava auditoria. | Evento `DOCUMENT_UPLOADED` com SHA-256 na auditoria; `sha256` na resposta do upload. | `test_upload_records_sha256_in_audit_trail` |
| T01a | P1 | CI dispara em `develop`, branch inexistente; a integracao usa `developer`. | Filtros do `ci.yml` apontam para `main` e `developer`. | Verificado com `git ls-remote` (sem execucao remota) |

---

## Abertos

| ID | Prio | Problema / evidencia | Acao minima | Dependencia | Esforco | Status |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| T05a | P0 | Nao ha identidade de usuario: `verify_api_key` aceita uma chave unica e, em `ENVIRONMENT=development/test`, **qualquer requisicao sem chave**. Segregacao de funcoes impossivel. | Identidade minima no servidor (ex.: mapa chave->usuario/papel via variavel de ambiente), nunca gravar a chave na auditoria. | D1 | 1-2 d | Bloqueado (D1) |
| T05b | P0 | RF09 inexistente: nao ha endpoint para aprovar, rejeitar ou registrar excecao. | `POST /compliance/reviews/{document_id}` append-only com decisao, justificativa obrigatoria, autor, timestamp; regra: autor da proposta nao aprova; migration 002. | T05a | 2-3 d | Bloqueado (D1) |
| T06b | P0 | UI sem fluxo de revisao humana nem exibicao de evidencias por pagina. | Painel de decisao no laudo; exibir `evidence` e trechos por pagina. | T05b | 2-3 d | Pendente |
| T09a | P0 | Compose + smoke nao executados nesta auditoria (Docker parado). | `make up && make smoke` em maquina da equipe; registrar saida no relatorio. | Docker | 0,5 d | Pendente |
| T04c | P1 | Dataset `edge_cases/sample_cnd_ilegivel.json` espera revisao manual; motor retorna `NON_COMPLIANT` (palavra-chave obrigatoria ausente). Unica divergencia restante nos evals. | Aplicar a politica decidida em D2. | D2 | 0,5 d | Bloqueado (D2) |
| T01b | P1 | Imagem Docker instala `backend/requirements.txt` (faixas `>=`, inclui pytest/black) e nao `requirements.lock`/`uv.lock`: build nao reprodutivel e diferente do dev/CI. | Instalar a partir de `requirements.lock` (exportado por `make uv-lock`) sem dependencias de dev. | - | 0,5 d | Pendente |
| T05c | P1 | `ENVIRONMENT` padrao e `development` e `DEBUG=True`: deploy sem `.env` correto fica sem autenticacao e expoe `str(exc)` em erro 500. | Padrao seguro (`production`, `DEBUG=False`) e bypass so com opt-in explicito. | T05a | 0,5 d | Pendente |
| T06c | P1 | Frontend nao envia `X-API-Key`; so funciona porque `development` libera acesso anonimo. | Enviar credencial do usuario (apos T05a). | T05a | 0,5 d | Pendente |
| T11 | P1 | Suite de backend leva ~5 min: `test_health_endpoint` e 2 testes de upload esperam ~60 s cada por timeout de MinIO/Redis reais; cada TestClient espera ~4 s pelo Postgres no `lifespan`. | Mockar storage/redis nesses testes; tornar `create_all` do lifespan configuravel. | - | 0,5 d | Pendente |
| T03c | P2 | Upload le o arquivo inteiro em memoria antes de checar 50 MB; erros 400/500 ecoam `str(e)`. | Leitura limitada (`MAX_FILE_SIZE + 1`); mensagens genericas ao cliente. | - | 0,5 d | Pendente |
| T07a | P2 | `nginx.conf` sem proxy `/api` nem `client_max_body_size`; compose usa o servidor de dev do Vite. | So necessario se a demo usar o build de producao. | - | 0,5 d | Adiado |
| T08b | P2 | Evals usam textos sinteticos (3 PDFs, 11 casos): nao medem OCR nem LLM. | Adicionar PDFs reais anonimizados por tipologia do MVP. | dados | 1 d | Pendente |
| T10b | P2 | Docs (`rules-engine.md`, `api-reference.md`) nao descrevem filtro por tipologia, `evaluated_rules`, `document_type`, `sha256`. | Atualizar apos estabilizar T05b. | T05b | 0,5 d | Pendente |

---

## Hipoteses da analise preliminar nao confirmadas

| Hipotese | Resultado da verificacao |
| :-- | :-- |
| Migrations divergentes dos modelos | **Nao confirmada**: `alembic upgrade head` + `alembic check` em SQLite descartavel: "No new upgrade operations detected". Risco real e outro: runtime usa `create_all`. |
| Divergencia entre gerenciadores de dependencias quebra o build local | Parcial: `uv lock --check` ok e `uv sync --frozen` ok; o problema real e a imagem Docker usar `requirements.txt` sem lock (T01b). |
| Ausencia de processamento assincrono | **Nao confirmada**: Celery + Redis implementados; worker exercitado em teste direto da tarefa. Nao foi validado com broker real. |
| `App.tsx` concentrado exige refatoracao | Nao priorizado: o defeito real era a fabricacao de dados (T06a). Extraido apenas o modulo testavel `presentation.ts`. |
| Upload sem validacao | **Nao confirmada**: extensao, magic bytes `%PDF` e 50 MB ja validados; `uuid` no nome evita path traversal. |

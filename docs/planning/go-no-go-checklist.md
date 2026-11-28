# Checklist Go/No-Go - Entrega MVP (M6)

Documento operacional da **Issue #64** (`M6 - Go/No-Go e entrega`), derivado dos critérios da
seção 5 de [Plano de Entrega](DELIVERY_PLAN_2026_12_05.md) e consolidado a partir de
[Relatório de Validação](VALIDATION_REPORT.md).

> **Data limite da decisão:** `27/11/2026` (M6), após o code freeze de `26/11/2026` (M5) e a
> publicação da RC1 `v1.0.0-rc.1` (`78e65a5` em `main`). Cronograma da auditoria de 23/11/2026
> (D4); as datas anteriores (freeze em 01/12, decisão em 04/12, entrega em 05/12) são históricas;
> apresentações seguem em `07` ou `09/12/2026`.
>
> **Estado verificado em 27/11/2026:** pré-avaliação consolidada sobre `origin/dev` (`035c255`,
> `CI` run [46093243049](https://github.com/conformia-bndes/conformia-platform/actions/runs/46093243049)
> e `CodeQL` run [46093242982](https://github.com/conformia-bndes/conformia-platform/actions/runs/46093242982)
> verdes) e `origin/main` (`78e65a5`, tag `v1.0.0-rc.1`) — decisão formal aguarda integração dos
> PRs de correção P1 pendentes e o ensaio ao vivo com Docker.

---

## 1. Matriz dos Critérios Obrigatórios de Go

| # | Critério (`DELIVERY_PLAN_2026_12_05.md` §5) | Estado em 27/11/2026 | Evidência verificada / Pendência objetiva |
| :- | :--- | :--- | :--- |
| 1 | `pytest`, `black --check`, `flake8`, `npm run lint`, `npm test`, `npm run build` e `python evals/eval_pipeline.py` aprovados no commit candidato | **OK em `dev` (`035c255`) e RC1 (`78e65a5`); revalidar no SHA final** | CI completo verde no run `46093243049` (`035c255`) e na regressão RC1 (`46049692868`, cobertura backend `92%`, frontend `24 passed`, `mkdocs build --strict` verde). Reconfirmar no commit final promovido para `main` após merge das P1 restantes. |
| 2 | Evals com **0 falsos positivos** | **OK (`0` falsos positivos; ampliação em `#166`)** | `evals/eval_pipeline.py` com **48/48 verificações**, **100,00%** de acurácia e **0 falsos positivos** (sem regressão contra `evals/baseline.json`). A `#162` fecha as lacunas de validade múltipla/termos/CNPJ e a `#166` (atribuída a `alanafeitosa-ui`) amplia a cobertura adversarial no gate. |
| 3 | `make up && make smoke` com código `0` no ambiente de demonstração | **OK (CI `Infra / Stack` 6/6 e estação local com Docker Desktop)** | Job `Infra / Stack` verde no CI e execução local de `make up && make smoke` com código `0` (`database: healthy`, `redis: healthy`, `minio: healthy`, `STARTED -> SUCCESS`, `overall_status=COMPLIANT`, revisão Maker-Checker `state=FINAL decision=APPROVE`). |
| 4 | Roteiro de demo executado de ponta a ponta (CND válida -> `COMPLIANT`, CND vencida -> `NON_COMPLIANT`, CND sem validade -> revisão manual, decisão humana na auditoria) | **OK (`#63` / PR #201)** | Roteiro executável ([demo-script.md](demo-script.md)), 8 PDFs fictícios verificados, `backend/tests/test_demo_flow.py` (`7/7`), OCR real no contêiner (`validate_ocr_container.py` + `cnd_federal_digitalizada_ocr.pdf` -> `COMPLIANT`) e ensaio ao vivo dos 5 atos contra a stack Docker (`http://localhost:5173` HTTP 200 e `http://localhost:8000`) concluídos com código `0`. |
| 5 | Revisão humana com segregação comprovada por teste (autor não aprova a própria decisão) | **OK (backend, UI, smoke CI e Docker local)** | Comprovado em `backend/tests/test_reviews.py`, `backend/tests/test_demo_flow.py`, `backend/scripts/smoke_test.py` (CI e local 6/6) e `frontend/src/components/HumanReviewPanel.tsx`. |
| 6 | Nenhum defeito bloqueador aberto; nenhum dado simulado apresentado como real | **Pendente de merge final das P1** | `0` dados simulados na UI/API; todas as issues atribuídas a `pedrohpsantos` (`#162` PR #195, `#163` PR #196, `#167` PR #197, `#174` PR #198, `#171` PR #200, `#63` PR #201) possuem PRs abertos com `CI OK` verde. Restam abertas issues P1 de outros responsáveis (`#55`, `#164`, `#165`, `#166`, `#168`), detalhadas na seção 2. |

---

## 2. Inventário de Pendências, Bloqueadores e Riscos Residuais (27/11/2026)

### 2.1 Estado dos PRs e Branches da Auditoria

- **PRs integrados na RC1:** `#125`, `#138`, `#146`, `#147`, `#177`, `#191`, `#192`, `#193`, `#194` (`v1.0.0-rc.1` publicada em `main`).
- **PRs abertos contra `dev` com CI verde (`pedrohpsantos`):** `#195` (`#162`), `#196` (`#163`), `#197` (`#167`), `#198` (`#174`), `#200` (`#171`), `#201` (`#63`).
- **Issues P1/P0 abertas em 27/11/2026:**

| Issue | Prioridade | Responsável | Situação em 27/11/2026 | Impacto no Go/No-Go |
| :--- | :---: | :--- | :--- | :--- |
| `#162` | `P1` | `pedrohpsantos` | PR [#195](https://github.com/conformia-bndes/conformia-platform/pull/195) aberto (`CI OK` verde) | Fecha falsos positivos por validade múltipla, termos impeditivos e ausência de CNPJ |
| `#163` | `P1` | `pedrohpsantos` | PR [#196](https://github.com/conformia-bndes/conformia-platform/pull/196) aberto (`CI OK` verde) | Fecha RBAC por rota, `performed_by` real e `ADR-005` (`RF01`) |
| `#167` | `P1` | `pedrohpsantos` | PR [#197](https://github.com/conformia-bndes/conformia-platform/pull/197) aberto (`CI OK` verde + PG 16 `23 passed, 0 skipped`) | Fecha imutabilidade append-only (triggers + `CHECK` constraints) no banco (`RNF03`) |
| `#63` | `P0` | `pedrohpsantos` | PR [#201](https://github.com/conformia-bndes/conformia-platform/pull/201) aberto (`make up && make smoke` + 5 atos + OCR ao vivo validados) | Critério Go 4 comprovado |
| `#64` | `P0` | `pedrohpsantos` | Esta matriz/ata consolidada com evidências reais | Decisão formal Go/No-Go |
| `#55` | `P1` | `Mateiki` | Aberta (branch remota `55-...` não mesclada) | Evidências por página na UI (`RF08`) |
| `#164` | `P1` | `arthurmgl99` | Aberta (branch remota `sec/isolar-dados-prod-celery-164` não mesclada) | Isolamento de dados no compose prod e validação de path no worker |
| `#165` | `P1` | `alanafeitosa-ui` | Aberta | Delimitação de prompt, truncamento e grounding semântico no Maker-Checker |
| `#166` | `P1` | `alanafeitosa-ui` | Aberta | Ampliação de tipologias e casos adversariais no gate de Evals |
| `#168` | `P1` | `Mateiki` | Aberta (PRs antigos já resolvidos; falta fechar registro do SHA final) | Governança de PRs e rastreabilidade do SHA avaliado |

> **Itens P2 (M7 — Pós-entrega, não bloqueiam Go):** `#58`, `#169`, `#170`, `#171`, `#172`, `#173`, `#174`.  
> **Itens fora do MVP (`fora-do-mvp`):** `#148`–`#152` (adiados formalmente conforme `DELIVERY_PLAN_2026_12_05.md`).

### 2.2 Riscos Residuais Conhecidos

- **Provedor LLM na demo (`#129`):** OpenRouter `:free` (`particle-ai/particle-1:free`) validado com dados sintéticos, sujeito a `HTTP 429` e política de retenção externa; usar estritamente PDFs fictícios de `docs/samples/` na demonstração e manter o Plano B `fail-closed` preparado. Para produção com dados reais, permanece necessária contratação de endpoint soberano em território nacional (LGPD / `RNF05`).
- **Dataset real anonimizado (`#58` / `T08b`):** permanece como risco residual aceito enquanto não houver acervo real anonimizado; os evals comprovam regressão determinística em textos e PDFs sintéticos.
- **Pacotes GHCR (`#102`):** confirmar visibilidade `Public` de `backend` e `frontend` no GHCR após a publicação da tag final e validar `docker pull` com `infra/docker-compose.ghcr.yml`.
- **TLS 1.3 em produção (`#172` / `RNF01`):** terminação TLS externa ao Nginx local deve ser comprovada via `openssl s_client -tls1_3` no ambiente de implantação real.

---

## 3. Ata de Decisão (Assinar após integração das P1 e ensaio ao vivo)

- **Data da reunião:** `____/____/2026`
- **Commit / Tag candidata avaliada:** `v1.0.0-rc.1` (`78e65a5`) / `dev` (`035c255`) — *atualizar para o SHA final de `main` após merge das P1*
- **Veredito preliminar em 27/11/2026 (não vinculante):** **Pendente de Go** até integração dos PRs `#162`, `#163`, `#167` (já prontos), resolução/decisão formal sobre `#55`, `#164`, `#165`, `#166`, `#168` e execução de `make up && make smoke` + ensaio ao vivo (`#63`).
- **Veredito final:**
  - `[ ]` **GO** — Todos os 6 critérios obrigatórios comprovados no commit candidato.
  - `[ ]` **GO COM RESTRIÇÕES** — Critérios 1–4 e 6 comprovados; restrições formalmente aceitas e registradas abaixo com responsáveis e prazo.
  - `[ ]` **NO-GO** — Falso positivo em evals, falha de smoke ou fluxo essencial sem comprovação.
- **Riscos residuais aceitos e responsáveis:**
  - *(Confirmar e assinar na reunião de decisão)*
- **Aprovadores:** Tech Lead (`pedrohpsantos`) e integrantes presentes.

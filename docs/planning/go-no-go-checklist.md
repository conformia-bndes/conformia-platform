# Checklist Go/No-Go - Entrega 05/12/2026

Documento operacional da **Issue #64** (`M6 - Go/No-Go e entrega`), derivado dos critérios da
seção 5 de [Plano de Entrega (05/12/2026)](DELIVERY_PLAN_2026_12_05.md) e consolidado a partir de
[Relatório de Validação](VALIDATION_REPORT.md).

> **Data limite da decisão:** `04/12/2026` (após Code Freeze em `01/12/2026`, RC1 `#62` e ensaio `#63`).
> **Estado em 22/11/2026:** pré-avaliação em andamento — decisão formal ainda **não emitida** até
> conclusão dos itens pendentes abaixo.

---

## 1. Matriz dos Critérios Obrigatórios de Go

| # | Critério (`DELIVERY_PLAN_2026_12_05.md` §5) | Estado em 22/11/2026 | Evidência / Pendência |
| :- | :--- | :--- | :--- |
| 1 | `pytest`, `black --check`, `flake8`, `npm run lint`, `npm test`, `npm run build` e `python evals/eval_pipeline.py` aprovados no commit candidato | **Parcial (commit atual em branch local; commit candidato final pendente)** | Verificação local executada no branch unificado; reexecutar no commit candidato final em `main` após sincronização `dev` <-> `main` e fechamento de RC1 (`#62`). |
| 2 | Evals com **0 falsos positivos** | **OK no código atual** | `evals/eval_pipeline.py` com `0` falsos positivos e `100%` de acurácia determinística; revalidar após merge de `#146` se entrar antes do freeze. |
| 3 | `make up && make smoke` com código `0` no ambiente de demonstração | **Parcial** | Passa no CI (`Infra / Stack`, PR #121 em `main` com 6 etapas); pendente execução ao vivo no ambiente de apresentação (Docker estava parado nesta estação em 22/11). |
| 4 | Roteiro de demo executado de ponta a ponta (CND válida -> `COMPLIANT`, CND vencida -> `NON_COMPLIANT`, CND sem validade -> revisão manual, decisão humana na auditoria) | **Parcial (`#63`)** | Roteiro ([demo-script.md](demo-script.md)), PDFs fictícios completos em `docs/samples/` e teste automatizado (`test_demo_flow.py`) implementados; falta ensaio ao vivo com Docker e apresentadores. |
| 5 | Revisão humana com segregação comprovada por teste (autor não aprova a própria decisão) | **OK (automatizado e smoke CI)** | Coberto em `backend/tests/test_reviews.py`, `backend/tests/test_demo_flow.py`, `backend/scripts/smoke_test.py` (PR #121) e `HumanReviewPanel.tsx` (PR #145 em `dev`). |
| 6 | Nenhum defeito bloqueador aberto; nenhum dado simulado apresentado como real | **Pendente** | Em 22/11 ainda existem pendências abertas: sincronização `main` <-> `dev`, PR #138 (timeout de upload / `resilience_test.sh`), PR #146 (revisão), validação manual de CD (`#102` visibilidade GHCR) e fechamento de RC1 (`#62`). |

---

## 2. Bloqueadores e Riscos Residuais a Avaliar em 04/12

- **Sincronização `main` <-> `dev` e PRs pendentes:** garantir que `T06b`/`T06c` (`#145`), `ADR-004` (`#144`), `#138` e a decisão sobre `#146`/`#134` estejam consolidados em `main` antes do corte da tag final.
- **Provedor LLM na demo (`#129`):** OpenRouter `:free` (`particle-ai/particle-1:free`) validado com dados sintéticos, porém sujeito a `HTTP 429` e retenção de dados; manter estritamente dados fictícios na demo, rotacionar a chave antes do evento e manter o plano B fail-closed preparado. Para uso com documentos reais em produção, permanece necessária decisão contratual/infraestrutura por endpoint corporativo sem retenção (LGPD / RNF05).
- **Dataset real anonimizado (`#58` / `T08b`):** caso não seja concluído até `26/11`, registrar como risco residual aceito (evals medem apenas regressão em textos e PDFs sintéticos).
- **Pacotes GHCR (`#102`):** confirmar visibilidade `Public` de `backend` e `frontend` no GHCR e teste de `docker pull` com `infra/docker-compose.ghcr.yml`.

---

## 3. Ata de Decisão (Preencher em 04/12/2026)

- **Data da reunião:** `____/12/2026`
- **Commit / Tag candidata avaliada:** `________________`
- **Veredito:**
  - `[ ]` **GO** — Todos os 6 critérios obrigatórios comprovados no commit candidato.
  - `[ ]` **GO COM RESTRIÇÕES** — Critérios 1–4 e 6 comprovados; item 5 substituído ou restrição formalmente aceita e documentada abaixo.
  - `[ ]` **NO-GO** — Falso positivo em evals, falha de smoke ou fluxo essencial sem comprovação.
- **Riscos residuais aceitos e responsáveis:**
  - *(Registrar na reunião de 04/12/2026)*
- **Aprovadores:** Tech Lead (`pedrohpsantos`) e integrantes presentes.

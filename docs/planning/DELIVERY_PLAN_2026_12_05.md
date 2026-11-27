# Plano de Entrega - MVP até 27/11/2026

Data de referência: **13/11/2026** (revisado em 21/11/2026). Base: branch de integração `dev`,
commit `627a95a`. Histórico: a primeira versão deste plano (29/10/2026) auditou o commit
`d76f41c`, quando a branch de integração ainda se chamava `developer`.

Este plano substitui hipóteses da análise preliminar por fatos verificados no código. O backlog
detalhado está em [IMPLEMENTATION_BACKLOG.md](IMPLEMENTATION_BACKLOG.md), as evidências de
execução em [VALIDATION_REPORT.md](VALIDATION_REPORT.md), o roteiro da apresentação em
[demo-script.md](demo-script.md) e o checklist operacional da decisão final em
[go-no-go-checklist.md](go-no-go-checklist.md).

> **Cronograma vigente (auditoria de 23/11/2026):** a entrega foi antecipada para **27/11/2026**.
> Milestones: M4 = 25/11, M5 (code freeze) = 26/11, M6 (Go/No-Go e entrega) = 27/11, M7 (pós-entrega) = 10/12. O prazo de 05/12/2026 (decisão D3, 01/11) é histórico. As
> apresentações seguem em 07 ou 09/12; os dias entre a entrega e a apresentação servem de folga
> para ensaio e correção de defeitos críticos. O `sprints-roadmap.md` é histórico.
>
> O nome do arquivo foi mantido para não quebrar links.

---

## 1. Escopo mínimo confirmado (MVP)

Derivado do "Cenário de Demonstração Mínima" (`sprints-roadmap.md` seção 4) e dos RF de
prioridade Alta (`requirements.md`).

| # | Fluxo essencial | Requisito | Estado em 13/11 |
| :- | :-- | :-- | :-- |
| 1 | Upload de PDF com validação (extensão, `%PDF-`, 50 MB) e armazenamento MinIO | RF02 | Implementado e testado; leitura limitada a 50 MB (T03c, PR #82). Exercitado em Compose pelo smoke do CI. |
| 2 | Extração nativa + OCR Tesseract por página, assíncrona via Celery | RF03 | Implementado; fila validada pelo smoke do CI. OCR no container validado na branch `docs/validar-compose-smoke-ocr` (issue #46), ainda não integrada. |
| 3 | Campos tipados com evidência (página + trecho) | RF04, RF08 | Implementado (regex). Coordenadas (`bounding_box`) sempre nulas. |
| 4 | Checklist declarativo + motor determinístico | RF05, RF06 | Corrigido (validade e tipologia, PR #44; política D2, PR #92). |
| 5 | Maker-Checker com citação literal obrigatória | RF07 | Fail-closed (PR #44). Sem chave LLM, regras híbridas vão para revisão manual. Modelo gratuito via OpenRouter avaliado em 13/11 (`docs/engineering/maker-checker.md`). |
| 6 | Laudo apresentado ao analista com status compreensíveis | RF08 | Corrigido (rótulos de revisão manual / não aplicável; sem dados simulados). Evidências por página na UI em andamento (T06b). |
| 7 | **Revisão humana: aprovar, rejeitar ou exceção motivada** | RF09 | API implementada e testada com segregação (chaves pessoais, D1; PRs #45 e #68). **UI pendente** (T06b, T06c). |
| 8 | Trilha de auditoria com executor, timestamp e hash do arquivo | RF10 | Implementado: hash SHA-256 no upload e eventos `REVIEW_*` com o analista. |
| 9 | Execução reproduzível em Docker Compose + smoke test | RNF04 | Migrations no startup (PR #109); smoke em Compose no job `smoke` de `ci-infra.yml` (PR #95). Registro manual com saída pendente de integração (T09a). |

**Tipologias obrigatórias propostas para o MVP:** `CND_FEDERAL` e `CRF_FGTS` (as duas citadas no
cenário de demonstração). `CNDT_TRABALHISTA` e `FALENCIA_RECUPERACAO` permanecem ativas (já tem
regra e detecção), mas não são critério de Go. `LICENCA_AMBIENTAL` tem regra e detecção no parser
(expressão de licença + órgão ambiental). Por ser regra HYBRID, sem LLM configurado uma licença
vigente resulta em revisão manual (Maker-Checker fail-closed). São reprovadas direto as licenças
com a frase exata "LICENÇA SUSPENSA" ou com "EMBARGADO" ("embargada" não é reconhecida). A licença
vencida só é reprovada se tiver os termos obrigatórios da regra ("LICENÇA AMBIENTAL", "VÁLIDA ATÉ",
"ÓRGÃO AMBIENTAL"); sem algum deles, vai para revisão manual.
`INTEGRIDADE_CEIS_CNEP` tem detecção no parser e regra HYBRID que exige os dois cadastros (CEIS e
CNEP) e "nada consta". Os termos de sanção definidos na regra reprovam direto, inclusive quando o
CEIS diz "nada consta" e o CNEP traz um desses termos (ex.: "multa aplicada"). Sem LLM
configurado, o restante vai para revisão manual; com LLM, só é aprovado se o Checker aprovar e a
citação existir no documento.

### Itens explicitamente adiados (fora do MVP)

| Item | Requisito | Motivo |
| :-- | :-- | :-- |
| Laudo pericial em PDF | RF11 | Exportação JSON pela API cobre a demonstração; PDF depende de definição de layout. |
| Dashboard de acurácia | RF12 | Prioridade média; dados atuais (poucos casos sintéticos) não sustentam métricas. |
| Conectores governamentais | RF13 | Exige credenciais e acordos externos inexistentes. |
| Alertas de vencimento e reprocessamento agendado | RF14, RF15 | Prioridade baixa; Celery Beat não configurado. |
| RBAC completo com JWT/IdP | RF01 | Sem IdP definido. Substituir por identidade mínima (seção 6). |
| OpenTelemetry e testes de carga | Sprint 7 | Sem infraestrutura de coleta definida. |

---

## 2. Caminho crítico e dependências

```text
[D1 decidida] -> [T05a/T05b concluidos] -> [T06c chave na UI] -> [T06b UI de revisao]
                                                                              |
[T09a smoke no CI (feito) + registro manual e OCR no container] --------------+--> [Ensaio de demo] -> [Go/No-Go 27/11]
[D2 decidida] -> [T04c concluido (PR #92)] -----------------------------------+
```

- Em 13/11, o caminho crítico é a UI de revisão (T06c, T06b). D1 e D2 estão decididas e
  implementadas; T05d (migrations no startup) está concluído.
- **T09a**: o smoke em Compose com PostgreSQL, Redis, MinIO e worker reais roda no CI
  (`ci-infra.yml`). Falta integrar o registro manual com saída e a validação de OCR no
  container (branch `docs/validar-compose-smoke-ocr`).
- Histórico (29/10): nenhum teste ponta a ponta com serviços reais havia sido executado.

---

## 3. Cronograma regressivo (revisado)

| Período | Objetivo | Critério de saída verificável | Status em 13/11 |
| :-- | :-- | :-- | :-- |
| 29/10-04/11 | Auditoria, correções P0 do motor e da UI, **decisões D1/D2**, smoke em compose | `make up && make smoke` com código 0 em máquina da equipe; D1 e D2 registradas | Concluído (histórico): P0 no PR #44; D1 em 29/10, D2 e D3 em 01/11 (PR #90); smoke no CI (PR #95) |
| **04/11** | **Congelamento de escopo** (tipologias e fluxos do MVP) | Este documento aprovado pelo responsável de produto | Escopo da seção 1 mantido; aprovação formal não registrada no repositório |
| 05/11-12/11 | Identidade mínima, endpoint de revisão humana append-only, migration 002 | Testes de autorização (próprio autor não aprova) e de persistência passando | Concluído: PRs #45, #68 (adiantados para 29/10), #109 (migrations), #110 (padrões seguros) |
| 13/11-19/11 | UI de revisão (aprovar/rejeitar/exceção com justificativa), evidências por página na UI | Fluxo upload -> laudo -> decisão humana exercitado em compose | Em andamento: T06c e T06b pendentes; evidências por página em branch |
| 20/11-24/11 | Integração ponta a ponta, smoke estendido (inclui verificação e decisão), evals ampliados com PDFs reais anonimizados | Fluxo completo no smoke do CI | Smoke estendido integrado (PR #121, 22/11); T06b/T06c integrados (PR #145, 22/11); PDFs reais pendentes (#58) |
| **25/11 (M4)** | Integração final e saneamento dos PRs abertos (issue #168) | Nenhum PR de entrega com CI vermelho ou conflito | - |
| **26/11 (M5)** | **Code freeze** e RC1 (#62) | Commit candidato definido | - |
| **27/11 (M6)** | **Go/No-Go e entrega** (#64) | Checklist da seção 5 preenchido com evidências no commit candidato | - |
| 10/12 (M7) | Pós-entrega: ensaio, apresentações (07 ou 09/12) e correções críticas | Sem funcionalidade nova | - |

As datas anteriores desta tabela (code freeze em 01/12, Go/No-Go em 04/12 e entrega em 05/12)
foram substituídas pelo cronograma da auditoria de 23/11/2026.

**Capacidade:** o tamanho e a disponibilidade da equipe não estão documentados no repositório;
não é possível calcular folga real. Estimativa de esforço P0 restante em 13/11: ~3 a 4,5
dias-pessoa (T06c 0,5-1, T06b 2-3, fechamento de T09a 0,5). Se a equipe tiver menos de 1,5 pessoa dedicada, reduzir
o escopo: revisão humana somente via API (sem UI própria) e demo com uma única tipologia (CND).

---

## 4. Riscos

| Risco | Impacto | Mitigação |
| :-- | :-- | :-- |
| Compose validado só no CI; registro manual e OCR no container fora de `dev` em 13/11 | Demo pode não subir no ambiente da equipe | Job `smoke` de `ci-infra.yml` roda em `main` e `dev`; integrar `docs/validar-compose-smoke-ocr` (T09a) |
| UI de revisão (T06c, T06b) não iniciada em 13/11 | RF09 só demonstrável via API | Plano B da seção 3: revisão humana pela API no roteiro de demo |
| Sem chave LLM no ambiente de demo | Regras HYBRID sempre em revisão manual | Comportamento correto e seguro; documentar no roteiro; MVP usa CND/CRF (determinísticas) |
| RULE-BNDES-006: sanção no CNEP escrita com outras palavras (ex.: "tipo de sanção: multa") não é bloqueada pela regra | Com LLM, CEIS "nada consta" + multa no CNEP pode sair `COMPLIANT` se o Maker-Checker aprovar | Mitigado: `manual_review_keywords` da RULE-BNDES-006 (multa, penalidade, tipo de sanção, sanção aplicada, leniência, punição, PAR) encaminha para revisão manual sem chamar o LLM; testes em `backend/tests/test_maker_checker_rules_005_006.py`. Residual: a consulta CEIS/CNEP não tem verificação de data de emissão. |
| OCR no container validado apenas em branch não integrada | PDFs digitalizados podem falhar na demo | Integrar o passo de OCR do CI (issue #46); usar PDF nativo como plano B |
| Evals com poucos casos sintéticos | Acurácia reportada não representa produção | Declarar limite; adicionar PDFs reais anonimizados até o freeze de 26/11 (T08b, #58) |

---

## 5. Critérios de versão candidata e Go/No-Go

**GO** somente se todos os itens obrigatórios forem comprovados com evidência em
`VALIDATION_REPORT.md`:

1. `pytest`, `black --check`, `flake8`, `npm run lint`, `npm test`, `npm run build` e
   `python evals/eval_pipeline.py` aprovados no commit candidato.
2. Evals com **0 falsos positivos** (qualquer aprovação onde a verdade não e COMPLIANT).
3. `make up && make smoke` com código 0 no ambiente de demonstração.
4. Roteiro de demo executado de ponta a ponta: CND valida -> COMPLIANT; CND vencida ->
   NON_COMPLIANT; CND sem validade -> revisão manual; decisão humana registrada na auditoria.
5. Revisão humana com segregação comprovada por teste (autor não aprova a própria decisão).
6. Nenhum defeito bloqueador aberto; nenhum dado simulado apresentado como real.

**GO COM RESTRIÇÕES:** itens 1-4 e 6 comprovados, item 5 substituído por revisão registrada
sem segregação, com a restrição declarada no roteiro e aceita formalmente pelo responsável.

**NO-GO:** qualquer falso positivo, smoke falhando ou fluxo essencial sem comprovação.

---

## 6. Decisões humanas necessárias

| ID | Decisão | Opções | Prazo |
| :-- | :-- | :-- | :-- |
| D1 | Como identificar analistas para revisão e segregação Maker-Checker humana | **Decidida em 29/10: (a) chaves de API pessoais mapeadas no servidor** (`API_USERS`). JWT/IdP fica fora do MVP. | - |
| D2 | Documento de tipologia reconhecida sem uma palavra-chave obrigatória (ex.: OCR ilegível) | **Decidida em 01/11: (b) `MANUAL_REVIEW_REQUIRED`.** Sem termo obrigatório não há prova de irregularidade, só falta de leitura: o analista decide. Termos impeditivos e validade vencida continuam `NON_COMPLIANT`. Implementação: T04c | - |
| D3 | Data oficial de entrega | Decidida em 01/11: 05/12/2026. **Substituída pela D4.** | - |
| D4 | Antecipação da entrega | **Decidida na auditoria de 23/11/2026: entrega em 27/11/2026.** M4 = 25/11, M5 (code freeze) = 26/11, M6 (Go/No-Go e entrega) = 27/11, M7 (pós-entrega) = 10/12. As apresentações seguem em 07 ou 09/12, sem funcionalidade nova após a entrega. | - |

---

## 7. Release e rollback

- **Code Freeze (26/11/2026):** de `2026-11-26` (M5) a `2026-12-09` (última apresentação, D4) o
  `pr-title.yml` bloqueia PRs do tipo `feat:`; seguem aceitos correções (`fix`, `sec`, `revert`),
  documentação, testes, `chore` e `refactor` sem funcionalidade nova.
- **Release Candidate RC1 (`v1.0.0-rc.1`):** gerada pelo fluxo automatizado do `release-please`
  (`release-please-config.json` com `prerelease: true`, `prerelease-type: "rc"` e
  `release-as: "1.0.0-rc.1"`), acionando o `cd.yml` para construir e validar as imagens do backend
  e do frontend a partir da tag `v1.0.0-rc.1`. Publicada em 27/11/2026 (PR #192); em seguida
  `prerelease`, `prerelease-type` e `release-as` foram removidos do `release-please-config.json`
  para que a próxima release não repita a `1.0.0-rc.1`.
- Release: tag anotada no commit aprovado; imagens construidas a partir do mesmo commit;
  `.env` gerado por `make env` (sem segredos versionados).
- Rollback de aplicação: subir a tag anterior (`git checkout <tag>` + `make up`).
- Rollback de banco: a migration 002 tem `downgrade` testado em SQLite descartável; testar
  **somente em banco descartável**. No ambiente de demo, preferir restaurar volume a partir de backup.
- Desde o PR #109, o schema vem só do Alembic (serviço `migrate` antes da API e do worker);
  `create_all` foi removido do startup. Toda tabela nova precisa de migration explícita.

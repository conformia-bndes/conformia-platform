# Plano de Entrega - MVP até 05/12/2026

Data de referência: 29/10/2026. Base auditada: branch `developer`, commit `d76f41c` (contém `e39217b`).

Este plano substitui hipóteses da análise preliminar por fatos verificados no código. O backlog
detalhado esta em [IMPLEMENTATION_BACKLOG.md](IMPLEMENTATION_BACKLOG.md) e as evidências de
execução em [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

> Divergência de prazo: `sprints-roadmap.md` fixa a entrega em **07/12/2026**; este plano usa
> **05/12/2026** (data mais restritiva, definida para esta execução). Confirmar a data oficial.

---

## 1. Escopo mínimo confirmado (MVP)

Derivado do "Cenário de Demonstração Mínima" (`sprints-roadmap.md` seção 4) e dos RF de
prioridade Alta (`requirements.md`).

| # | Fluxo essencial | Requisito | Estado em 29/10 |
| :- | :-- | :-- | :-- |
| 1 | Upload de PDF com validação (extensão, `%PDF-`, 50 MB) e armazenamento MinIO | RF02 | Implementado e testado (unitário). Sem validação em compose nesta maquina. |
| 2 | Extração nativa + OCR Tesseract por página, assíncrona via Celery | RF03 | Implementado; OCR real não testado aqui (Tesseract ausente). |
| 3 | Campos tipados com evidência (página + trecho) | RF04, RF08 | Implementado (regex). Coordenadas (`bounding_box`) sempre nulas. |
| 4 | Checklist declarativo + motor determinístico | RF05, RF06 | Corrigido nesta execução (validade e tipologia). |
| 5 | Maker-Checker com citação literal obrigatória | RF07 | Corrigido para fail-closed. Sem chave LLM, regras híbridas vao para revisão manual. |
| 6 | Laudo apresentado ao analista com status compreensíveis | RF08 | Corrigido (rotulos de revisão manual / não aplicável; sem dados simulados). |
| 7 | **Revisão humana: aprovar, rejeitar ou exceção motivada** | RF09 | API implementada e testada com segregação (chaves pessoais, D1). **UI pendente** (T06b, T06c). |
| 8 | Trilha de auditoria com executor, timestamp e hash do arquivo | RF10 | Implementado: hash SHA-256 no upload e eventos `REVIEW_*` com o analista. |
| 9 | Execução reproduzível em Docker Compose + smoke test | RNF04 | Arquivos existem; **não executado** nesta maquina (Docker parado). |

**Tipologias obrigatórias propostas para o MVP:** `CND_FEDERAL` e `CRF_FGTS` (as duas citadas no
cenário de demonstração). `CNDT_TRABALHISTA` e `FALENCIA_RECUPERACAO` permanecem ativas (já tem
regra e detecção), mas não são critério de Go. `LICENCA_AMBIENTAL` e `INTEGRIDADE_CEIS_CNEP` tem
regra, porém **não tem detecção de tipologia no parser**: hoje sempre resultam em revisão manual.

### Itens explicitamente adiados (fora do MVP)

| Item | Requisito | Motivo |
| :-- | :-- | :-- |
| Laudo pericial em PDF | RF11 | Exportação JSON pela API cobre a demonstração; PDF depende de definição de layout. |
| Dashboard de acurácia | RF12 | Prioridade media; dados atuais (poucos casos sintéticos) não sustentam métricas. |
| Conectores governamentais | RF13 | Exige credenciais e acordos externos inexistentes. |
| Alertas de vencimento e reprocessamento agendado | RF14, RF15 | Prioridade baixa; Celery Beat não configurado. |
| RBAC completo com JWT/IdP | RF01 | Sem IdP definido. Substituir por identidade mínima (seção 6). |
| OpenTelemetry e testes de carga | Sprint 7 | Sem infraestrutura de coleta definida. |

---

## 2. Caminho crítico e dependências

```text
[D1 decidida] -> [T05a/T05b concluidos] -> [T06c chave na UI] -> [T06b UI de revisao]
                                                                              |
[T09 Compose + smoke em maquina com Docker] ----------------------------------+--> [Ensaio de demo] -> [Go/No-Go 04/12]
[D2 Politica para palavra-chave ausente] -> [T04c ajuste de regra + evals] ---+
```

- **D1** foi decidida (chaves pessoais); a API de revisão existe. O caminho crítico passa a
  ser a UI de revisão (T06c, T06b) e a validação em compose com PostgreSQL (T09a, T05d).
- **T09** precisa de uma maquina com Docker ativo; nenhum teste ponta a ponta com Postgres,
  Redis, MinIO e worker reais foi executado nesta auditoria.

---

## 3. Cronograma regressivo (revisado)

| Período | Objetivo | Critério de saida verificável |
| :-- | :-- | :-- |
| 29/10-04/11 | Auditoria, correções P0 do motor e da UI (feito), **decisões D1/D2**, smoke em compose | `make up && make smoke` com código 0 em maquina da equipe; D1 e D2 registradas |
| **04/11** | **Congelamento de escopo** (tipologias e fluxos do MVP) | Este documento aprovado pelo responsável de produto |
| 05/11-12/11 | Identidade mínima, endpoint de revisão humana append-only, migration 002 | Testes de autorização (próprio autor não aprova) e de persistência passando |
| 13/11-19/11 | UI de revisão (aprovar/rejeitar/exceção com justificativa), evidências por página na UI | Fluxo upload -> laudo -> decisão humana exercitado em compose |
| 20/11-26/11 | Integração ponta a ponta, smoke estendido (inclui verificação e decisão), evals ampliados com PDFs reais anonimizados | **Congelamento de funcionalidades em 26/11** |
| 27/11-01/12 | Correções, regressão completa, RC1 | **Code freeze em 01/12** (30/11 e feriado no DF: considerar disponibilidade) |
| 02/12-04/12 | Ensaio da demonstração, smoke em ambiente de demo, **Go/No-Go em 04/12** | Checklist da seção 5 preenchido com evidências |
| 05/12 | Entrega | Versão etiquetada, roteiro de demo executado |

**Capacidade:** o tamanho e a disponibilidade da equipe não estão documentados no repositório;
não e possível calcular folga real. Estimativa de esforço P0 restante: ~6 a 9 dias-pessoa
(T05a 1-2, T05b 2-3, T06 2-3, T09 1). Se a equipe tiver menos de 1,5 pessoa dedicada, reduzir
o escopo: revisão humana somente via API (sem UI própria) e demo com uma única tipologia (CND).

---

## 4. Riscos

| Risco | Impacto | Mitigação |
| :-- | :-- | :-- |
| Compose nunca validado nesta auditoria | Demo pode não subir | T09 até 04/11 em maquina com Docker; CI job `smoke` agora roda em `developer` |
| D1 não decidida até 05/11 | RF09 inviável; demo perde a intervenção do analista | Proposta de identidade mínima pronta (backlog T05a) |
| Sem chave LLM no ambiente de demo | Regras HYBRID sempre em revisão manual | Comportamento correto e seguro; documentar no roteiro; MVP usa CND/CRF (determinísticas) |
| OCR não validado (Tesseract ausente localmente) | PDFs digitalizados podem falhar na demo | Validar no container (imagem já instala Tesseract `por`); usar PDF nativo como plano B |
| Evals com poucos casos sintéticos | Acurácia reportada não representa produção | Declarar limite; adicionar PDFs reais anonimizados até 26/11 |
| Testes de backend lentos (~5 min) por timeouts de rede | CI lento, feedback tardio | Backlog T11 (mockar storage/health) |

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

**GO COM RESTRIÇÕES:** itens 1-4 e 6 comprovados, item 5 substituido por revisão registrada
sem segregação, com a restrição declarada no roteiro e aceita formalmente pelo responsável.

**NO-GO:** qualquer falso positivo, smoke falhando ou fluxo essencial sem comprovação.

---

## 6. Decisões humanas necessárias

| ID | Decisão | Opções | Prazo |
| :-- | :-- | :-- | :-- |
| D1 | Como identificar analistas para revisão e segregação Maker-Checker humana | **Decidida em 29/10: (a) chaves de API pessoais mapeadas no servidor** (`API_USERS`). JWT/IdP fica fora do MVP. | - |
| D2 | Documento de tipologia reconhecida sem uma palavra-chave obrigatória (ex.: OCR ilegível) | (a) `NON_COMPLIANT` (atual); (b) `MANUAL_REVIEW_REQUIRED` (o que o dataset `edge_cases` espera) | 04/11 |
| D3 | Data oficial de entrega | 05/12 (este plano) ou 07/12 (`sprints-roadmap.md`) | 31/10 |

---

## 7. Release e rollback

- Release: tag anotada no commit aprovado; imagens construidas a partir do mesmo commit;
  `.env` gerado por `make env` (sem segredos versionados).
- Rollback de aplicação: subir a tag anterior (`git checkout <tag>` + `make up`).
- Rollback de banco: a migration 002 (futura) deve ter `downgrade` testado **somente em banco
  descartável**; no ambiente de demo, preferir restaurar volume a partir de backup.
- Observação: hoje o backend cria tabelas com `create_all` no startup, e não via Alembic.
  A migration 001 coincide com os modelos (verificado com `alembic check`), mas qualquer
  tabela nova precisa de migration explicita.

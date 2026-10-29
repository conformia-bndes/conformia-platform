# Plano de Entrega - MVP ate 05/12/2026

Data de referencia: 29/10/2026. Base auditada: branch `developer`, commit `d76f41c` (contem `e39217b`).

Este plano substitui hipoteses da analise preliminar por fatos verificados no codigo. O backlog
detalhado esta em [IMPLEMENTATION_BACKLOG.md](IMPLEMENTATION_BACKLOG.md) e as evidencias de
execucao em [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

> Divergencia de prazo: `sprints-roadmap.md` fixa a entrega em **07/12/2026**; este plano usa
> **05/12/2026** (data mais restritiva, definida para esta execucao). Confirmar a data oficial.

---

## 1. Escopo minimo confirmado (MVP)

Derivado do "Cenario de Demonstracao Minima" (`sprints-roadmap.md` secao 4) e dos RF de
prioridade Alta (`requirements.md`).

| # | Fluxo essencial | Requisito | Estado em 29/10 |
| :- | :-- | :-- | :-- |
| 1 | Upload de PDF com validacao (extensao, `%PDF-`, 50 MB) e armazenamento MinIO | RF02 | Implementado e testado (unitario). Sem validacao em compose nesta maquina. |
| 2 | Extracao nativa + OCR Tesseract por pagina, assincrona via Celery | RF03 | Implementado; OCR real nao testado aqui (Tesseract ausente). |
| 3 | Campos tipados com evidencia (pagina + trecho) | RF04, RF08 | Implementado (regex). Coordenadas (`bounding_box`) sempre nulas. |
| 4 | Checklist declarativo + motor deterministico | RF05, RF06 | Corrigido nesta execucao (validade e tipologia). |
| 5 | Maker-Checker com citacao literal obrigatoria | RF07 | Corrigido para fail-closed. Sem chave LLM, regras hibridas vao para revisao manual. |
| 6 | Laudo apresentado ao analista com status compreensiveis | RF08 | Corrigido (rotulos de revisao manual / nao aplicavel; sem dados simulados). |
| 7 | **Revisao humana: aprovar, rejeitar ou excecao motivada** | RF09 | API implementada e testada com segregacao (chaves pessoais, D1). **UI pendente** (T06b, T06c). |
| 8 | Trilha de auditoria com executor, timestamp e hash do arquivo | RF10 | Implementado: hash SHA-256 no upload e eventos `REVIEW_*` com o analista. |
| 9 | Execucao reproduzivel em Docker Compose + smoke test | RNF04 | Arquivos existem; **nao executado** nesta maquina (Docker parado). |

**Tipologias obrigatorias propostas para o MVP:** `CND_FEDERAL` e `CRF_FGTS` (as duas citadas no
cenario de demonstracao). `CNDT_TRABALHISTA` e `FALENCIA_RECUPERACAO` permanecem ativas (ja tem
regra e deteccao), mas nao sao criterio de Go. `LICENCA_AMBIENTAL` e `INTEGRIDADE_CEIS_CNEP` tem
regra, porem **nao tem deteccao de tipologia no parser**: hoje sempre resultam em revisao manual.

### Itens explicitamente adiados (fora do MVP)

| Item | Requisito | Motivo |
| :-- | :-- | :-- |
| Laudo pericial em PDF | RF11 | Exportacao JSON pela API cobre a demonstracao; PDF depende de definicao de layout. |
| Dashboard de acuracia | RF12 | Prioridade media; dados atuais (poucos casos sinteticos) nao sustentam metricas. |
| Conectores governamentais | RF13 | Exige credenciais e acordos externos inexistentes. |
| Alertas de vencimento e reprocessamento agendado | RF14, RF15 | Prioridade baixa; Celery Beat nao configurado. |
| RBAC completo com JWT/IdP | RF01 | Sem IdP definido. Substituir por identidade minima (secao 6). |
| OpenTelemetry e testes de carga | Sprint 7 | Sem infraestrutura de coleta definida. |

---

## 2. Caminho critico e dependencias

```text
[D1 decidida] -> [T05a/T05b concluidos] -> [T06c chave na UI] -> [T06b UI de revisao]
                                                                              |
[T09 Compose + smoke em maquina com Docker] ----------------------------------+--> [Ensaio de demo] -> [Go/No-Go 04/12]
[D2 Politica para palavra-chave ausente] -> [T04c ajuste de regra + evals] ---+
```

- **D1** foi decidida (chaves pessoais); a API de revisao existe. O caminho critico passa a
  ser a UI de revisao (T06c, T06b) e a validacao em compose com PostgreSQL (T09a, T05d).
- **T09** precisa de uma maquina com Docker ativo; nenhum teste ponta a ponta com Postgres,
  Redis, MinIO e worker reais foi executado nesta auditoria.

---

## 3. Cronograma regressivo (revisado)

| Periodo | Objetivo | Criterio de saida verificavel |
| :-- | :-- | :-- |
| 29/10-04/11 | Auditoria, correcoes P0 do motor e da UI (feito), **decisoes D1/D2**, smoke em compose | `make up && make smoke` com codigo 0 em maquina da equipe; D1 e D2 registradas |
| **04/11** | **Congelamento de escopo** (tipologias e fluxos do MVP) | Este documento aprovado pelo responsavel de produto |
| 05/11-12/11 | Identidade minima, endpoint de revisao humana append-only, migration 002 | Testes de autorizacao (proprio autor nao aprova) e de persistencia passando |
| 13/11-19/11 | UI de revisao (aprovar/rejeitar/excecao com justificativa), evidencias por pagina na UI | Fluxo upload -> laudo -> decisao humana exercitado em compose |
| 20/11-26/11 | Integracao ponta a ponta, smoke estendido (inclui verificacao e decisao), evals ampliados com PDFs reais anonimizados | **Congelamento de funcionalidades em 26/11** |
| 27/11-01/12 | Correcoes, regressao completa, RC1 | **Code freeze em 01/12** (30/11 e feriado no DF: considerar disponibilidade) |
| 02/12-04/12 | Ensaio da demonstracao, smoke em ambiente de demo, **Go/No-Go em 04/12** | Checklist da secao 5 preenchido com evidencias |
| 05/12 | Entrega | Versao etiquetada, roteiro de demo executado |

**Capacidade:** o tamanho e a disponibilidade da equipe nao estao documentados no repositorio;
nao e possivel calcular folga real. Estimativa de esforco P0 restante: ~6 a 9 dias-pessoa
(T05a 1-2, T05b 2-3, T06 2-3, T09 1). Se a equipe tiver menos de 1,5 pessoa dedicada, reduzir
o escopo: revisao humana somente via API (sem UI propria) e demo com uma unica tipologia (CND).

---

## 4. Riscos

| Risco | Impacto | Mitigacao |
| :-- | :-- | :-- |
| Compose nunca validado nesta auditoria | Demo pode nao subir | T09 ate 04/11 em maquina com Docker; CI job `smoke` agora roda em `developer` |
| D1 nao decidida ate 05/11 | RF09 inviavel; demo perde a intervencao do analista | Proposta de identidade minima pronta (backlog T05a) |
| Sem chave LLM no ambiente de demo | Regras HYBRID sempre em revisao manual | Comportamento correto e seguro; documentar no roteiro; MVP usa CND/CRF (deterministicas) |
| OCR nao validado (Tesseract ausente localmente) | PDFs digitalizados podem falhar na demo | Validar no container (imagem ja instala Tesseract `por`); usar PDF nativo como plano B |
| Evals com poucos casos sinteticos | Acuracia reportada nao representa producao | Declarar limite; adicionar PDFs reais anonimizados ate 26/11 |
| Testes de backend lentos (~5 min) por timeouts de rede | CI lento, feedback tardio | Backlog T11 (mockar storage/health) |

---

## 5. Criterios de versao candidata e Go/No-Go

**GO** somente se todos os itens obrigatorios forem comprovados com evidencia em
`VALIDATION_REPORT.md`:

1. `pytest`, `black --check`, `flake8`, `npm run lint`, `npm test`, `npm run build` e
   `python evals/eval_pipeline.py` aprovados no commit candidato.
2. Evals com **0 falsos positivos** (qualquer aprovacao onde a verdade nao e COMPLIANT).
3. `make up && make smoke` com codigo 0 no ambiente de demonstracao.
4. Roteiro de demo executado de ponta a ponta: CND valida -> COMPLIANT; CND vencida ->
   NON_COMPLIANT; CND sem validade -> revisao manual; decisao humana registrada na auditoria.
5. Revisao humana com segregacao comprovada por teste (autor nao aprova a propria decisao).
6. Nenhum defeito bloqueador aberto; nenhum dado simulado apresentado como real.

**GO COM RESTRICOES:** itens 1-4 e 6 comprovados, item 5 substituido por revisao registrada
sem segregacao, com a restricao declarada no roteiro e aceita formalmente pelo responsavel.

**NO-GO:** qualquer falso positivo, smoke falhando ou fluxo essencial sem comprovacao.

---

## 6. Decisoes humanas necessarias

| ID | Decisao | Opcoes | Prazo |
| :-- | :-- | :-- | :-- |
| D1 | Como identificar analistas para revisao e segregacao Maker-Checker humana | **Decidida em 29/10: (a) chaves de API pessoais mapeadas no servidor** (`API_USERS`). JWT/IdP fica fora do MVP. | - |
| D2 | Documento de tipologia reconhecida sem uma palavra-chave obrigatoria (ex.: OCR ilegivel) | (a) `NON_COMPLIANT` (atual); (b) `MANUAL_REVIEW_REQUIRED` (o que o dataset `edge_cases` espera) | 04/11 |
| D3 | Data oficial de entrega | 05/12 (este plano) ou 07/12 (`sprints-roadmap.md`) | 31/10 |

---

## 7. Release e rollback

- Release: tag anotada no commit aprovado; imagens construidas a partir do mesmo commit;
  `.env` gerado por `make env` (sem segredos versionados).
- Rollback de aplicacao: subir a tag anterior (`git checkout <tag>` + `make up`).
- Rollback de banco: a migration 002 (futura) deve ter `downgrade` testado **somente em banco
  descartavel**; no ambiente de demo, preferir restaurar volume a partir de backup.
- Observacao: hoje o backend cria tabelas com `create_all` no startup, e nao via Alembic.
  A migration 001 coincide com os modelos (verificado com `alembic check`), mas qualquer
  tabela nova precisa de migration explicita.

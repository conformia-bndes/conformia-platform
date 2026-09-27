# ADR-001: Adocao de Monorepo Modular e Harness Engineering

## Metadados
- **Status**: Aprovado
- **Data**: 2026-09-26
- **Autores**: Equipe de Engenharia Conform.IA BNDES
- **Revisores**: @conformia-bndes/maintainers, @conformia-bndes/devops, @conformia-bndes/backend
- **Epico / Requisito**: Consulta Publica BNDES no 01/2025

---

## 1. Contexto e Declaracao do Problema
O desenvolvimento do Conform.IA BNDES exige a integracao coordenada de multiplos subsistemas interdependentes:
- Extracao documental e OCR (IDP em Python).
- Motor de regras normativas declarativas (JSON Schemas).
- Orquestracao de agentes de IA com avaliacao Maker-Checker (Harness Engineering).
- Interface de revisao de laudos para analistas de credito (React/TypeScript).
- Infraestrutura local conteinerizada para auditoria e demonstracao.

A dispersao desses componentes em multiplos repositorios isolados (polyrepo) dificultaria o alinhamento de esquemas de dados, geraria atrito no versionamento sincronizado de regras de compliance e encareceria a execucao de testes de regressao de ponta a ponta (Evals).

---

## 2. Opcoes Consideradas

### Opcao 1: Multiplos Repositorios Independentes (Polyrepo)
- Repositorios separados para `backend`, `frontend`, `rules` e `infra`.
- *Vantagens*: Isolamento estrito de permissoes de commit por equipe.
- *Desvantagens*: Complexidade de sincronizacao de contratos de API e JSON schemas de regras; dificuldade para inicializacao local unificada via Docker Compose; pipelines de CI fragmentados.

### Opcao 2: Monorepo Modular Unificado (Opcao Escolhida)
- Repositorio unico `conformia-platform` com delimitacao estrita de pastas, governanca por `CODEOWNERS`, CI com path-filtering e orquestracao via `infra/docker-compose.yml`.
- *Vantagens*: Atômica rastreabilidade de mudancas; sincronizacao imediata entre schemas de regras, pipeline de extracao e contratos do frontend; facilidade para auditorias de conformidade do BNDES.
- *Desvantagens*: Necessidade de controle rigoroso de governanca de revisao e acionamento condicional de CI.

---

## 3. Decisao Adotada
Adota-se a estrategia de **Monorepo Modular Unificado** complementada por diretrizes de **Harness Engineering**. 

As fronteiras de codigo sao estabelecidas por pastas especializadas com proprietarios designados em `.github/CODEOWNERS`:
- Infraestrutura: `infra/`
- Backend e IDP: `backend/`
- Schemas Normativos: `rules/schemas/`
- Benchmarks de Regressao: `evals/`
- Frontend: `frontend/`
- Documentacao: `docs/`
- Contexto de Agentes: `.agents/`

---

## 4. Consequencias e Compensacoes (Trade-offs)

### Impactos Positivos
- **Coerencia de Versoes**: Alteracoes em esquemas normativos (`rules/schemas/`) sao testadas simultaneamente contra o extrator IDP e o frontend no mesmo commit.
- **Ambiente Local Reprodutivel**: O comando `make up` sobe todo o ecossistema (Postgres, Redis, MinIO, Backend, Worker, Frontend) de forma consistente.
- **Execucao Eficiente de CI**: O uso de filtros de caminho (`dorny/paths-filter`) no GitHub Actions evita execucoes redundantes em jobs nao afetados pela mudanca.

### Impactos Negativos e Riscos
- **Risco de Dependencias Cruzadas Nao Intencionais**: Mitigado pela proibicao de importacoes relativas entre modulos independentes e testes estritos de isolamento.
- **Tamanho do Repositorio**: Mitigado pela higienizacao de arquivos binarios e uso do MinIO para armazenamento de amostras pesadas de PDFs.

---

## 5. Diretrizes de Implementacao e Auditoria
1. O pipeline de integracao continua deve garantir o acionamento apenas dos jobs correspondentes aos caminhos alterados no PR.
2. Todo PR deve comprovar conformidade com a checklist do `PULL_REQUEST_TEMPLATE.md`.
3. Testes de regressao em `evals/eval_pipeline.py` devem ser aprovados antes da integracao na branch `main`.

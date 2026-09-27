# ADR-001: Adoção de Monorepo Modular e Harness Engineering

## Metadados

- **Status**: Aprovado
- **Data**: 2026-09-26
- **Autores**: Equipe de Engenharia Conform.IA BNDES
- **Revisores**: @conformia-bndes/maintainers, @conformia-bndes/devops, @conformia-bndes/backend
- **Épico / Requisito**: Consulta Pública BNDES nº 01/2025

---

## 1. Contexto e Declaração do Problema

O desenvolvimento do Conform.IA BNDES exige a integração coordenada de múltiplos subsistemas interdependentes:

- Extração documental e OCR (IDP em Python).
- Motor de regras normativas declarativas (JSON Schema).
- Orquestração de agentes de IA com avaliação Maker-Checker (Harness Engineering).
- Interface de revisão de laudos para analistas de crédito (React/TypeScript).
- Infraestrutura local conteinerizada para auditoria e demonstração.

A dispersão desses componentes em múltiplos repositórios isolados (polyrepo) dificultaria o alinhamento de esquemas de dados, geraria atrito no versionamento sincronizado de regras de compliance e encareceria a execução de testes de regressão de ponta a ponta (Evals).

---

## 2. Opções Consideradas

### Opção 1: Múltiplos Repositórios Independentes (Polyrepo)

- Repositórios separados para `backend`, `frontend`, `rules` e `infra`.
- _Vantagens_: Isolamento estrito de permissões de commit por equipe.
- _Desvantagens_: Complexidade de sincronização de contratos de API e esquemas JSON de regras; dificuldade para inicialização local unificada via Docker Compose; pipelines de CI fragmentados.

### Opção 2: Monorepo Modular Unificado (Opção Escolhida)

- Repositório único `conformia-platform` com delimitação estrita de pastas, governança por `CODEOWNERS`, CI com path filtering e orquestração via `infra/docker-compose.yml`.
- _Vantagens_: Rastreabilidade atômica de mudanças; sincronização imediata entre esquemas de regras, pipeline de extração e contratos do frontend; facilidade para auditorias de conformidade do BNDES.
- _Desvantagens_: Necessidade de controle rigoroso de governança de revisão e acionamento condicional de CI.

---

## 3. Decisão Adotada

Adota-se a estratégia de **Monorepo Modular Unificado**, complementada por diretrizes de **Harness Engineering**.

As fronteiras de código são estabelecidas por pastas especializadas com proprietários designados em `.github/CODEOWNERS`:

- Infraestrutura: `infra/`
- Backend e IDP: `backend/`
- Esquemas normativos: `rules/schemas/`
- Benchmarks de regressão: `evals/`
- Frontend: `frontend/`
- Documentação: `docs/`
- Contexto de Agentes: `.agents/`

---

## 4. Consequências e Compensações (Trade-offs)

### Impactos Positivos

- **Coerência de Versões**: Alterações em esquemas normativos (`rules/schemas/`) são testadas simultaneamente contra o extrator IDP e o frontend no mesmo commit.
- **Ambiente Local Reprodutível**: O comando `make up` inicia todo o ecossistema (Postgres, Redis, MinIO, backend, worker e frontend) de forma consistente.
- **Execução Eficiente de CI**: O uso de filtros de caminho (`dorny/paths-filter`) no GitHub Actions evita execuções redundantes em jobs não afetados pela mudança.

### Impactos Negativos e Riscos

- **Risco de Dependências Cruzadas Não Intencionais**: Mitigado pela proibição de importações relativas entre módulos independentes e por testes estritos de isolamento.
- **Tamanho do Repositório**: Mitigado pela higienização de arquivos binários e pelo uso do MinIO para armazenamento de amostras pesadas de PDFs.

---

## 5. Diretrizes de Implementação e Auditoria

1. O pipeline de integração contínua deve acionar apenas os jobs correspondentes aos caminhos alterados no PR.
2. Todo PR deve comprovar conformidade com o checklist de `PULL_REQUEST_TEMPLATE.md`.
3. Os testes de regressão em `evals/eval_pipeline.py` devem ser aprovados antes da integração na branch `main`.

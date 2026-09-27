# Conform.IA BNDES - Documentacao Tecnica

Bem-vindo ao portal de documentacao tecnica e engenharia do **Conform.IA BNDES**, plataforma SaaS voltada para o Processamento Inteligente de Documentos (IDP), verificacao automatizada de conformidade cadastral e regulatoria, e auditoria imutavel no contexto da Consulta Publica BNDES no 01/2025.

---

## Finalidade do Sistema

O Conform.IA BNDES automatiza o ciclo completo de admissibilidade documental para proponentes de operacoes de financiamento e investimento no BNDES. O sistema foi projetado para eliminar gargalos de analise manual, garantir conformidade legal estrita (tolerancia zero a fraudes e pendencias) e oferecer rastreabilidade probatoria auditavel para orgaos de controle interno e externo (CGU, TCU).

---

## Pilares Estruturais da Solucao

1. **Ingestao Documental e IDP**: Extracao hibrida de texto e tabelas via analise vetorial nativa e OCR Tesseract com suporte ao idioma portugues.
2. **Motor de Regras Declarativo**: Avaliacao deterministica de requisitos legais e editalicios estruturados em JSON Schema.
3. **Harness Engineering e Padrao Maker-Checker**: Agentes de linguagem atuando sob contexto restrito e avaliacao independente de evidencias textuais para eliminacao de alucinacoes.
4. **Trilha de Auditoria Transacional**: Persistencia de logs de decisao, pontuacao e justificativas tecnicas em banco de dados relacional (PostgreSQL).

---

## Mapa da Documentacao

A documentacao esta organizada nos seguintes modulos:

- **Planejamento**:
  - [Planejamento do Projeto](planning/project-plan.md): Parametros, requisitos RF01-RF15, arquitetura, sprints e metas ate 07/12/2026.
- **Arquitetura**:
  - [Visao Geral](architecture/overview.md): Diagrama de blocos, componentes e fluxo de dados.
  - [Decisoes Arquiteturais (ADRs)](architecture/adr-index.md): Registro formal de decisoes tecnicas e compensacoes estruturais.
- **Desafio BNDES**:
  - [Analise do Edital](bndes/compliance-matrix.md): Mapeamento dos requisitos da Consulta Publica no 01/2025.
  - [Tipologias de Documentos](bndes/document-types.md): Especificacoes de certidoes federais, trabalhistas, societarias e ambientais.
- **Engenharia**:
  - [Pipeline IDP](engineering/idp-pipeline.md): Arquitetura de extracao textual, tabular e OCR.
  - [Motor de Regras](engineering/rules-engine.md): Avaliacao deterministica e hibrida.
  - [Harness e Avaliacao de IA](engineering/harness-evals.md): Protocolos de avaliacao continua, metricas e benchmarks.

---

## Repositorio e Links Uteis

- Repositorio Oficial: [https://github.com/conformia-bndes/conformia-platform](https://github.com/conformia-bndes/conformia-platform)
- Documentacao Publicada: [https://conformia-bndes.github.io/conformia-platform/](https://conformia-bndes.github.io/conformia-platform/)
- API Swagger UI Local: `http://localhost:8000/docs`
- Console MinIO Local: `http://localhost:9001`

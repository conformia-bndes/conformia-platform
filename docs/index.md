<div class="hero-section" markdown>

<div class="hero-pill">
  <span class="status-indicator"></span> Consulta Publica BNDES no 01/2025
</div>

<h1 class="hero-title">Conform.IA BNDES</h1>

<p class="hero-subtitle">
  Plataforma SaaS de <strong>Intelligent Document Processing (IDP)</strong> e <strong>Auditoria Imutavel</strong> concebida para automatizar a conferencia cadastral, fiscal, trabalhista e regulatoria de proponentes e operacoes de credito e investimento no BNDES.
</p>

<div class="hero-actions">
  <a href="development/quickstart/" class="btn btn-primary">
    Guia de Inicio Rapido
  </a>
  <a href="planning/" class="btn btn-secondary">
    Explorar Planejamento
  </a>
  <a href="https://github.com/conformia-bndes/conformia-platform" target="_blank" class="btn btn-secondary">
    Repositorio GitHub
  </a>
</div>

</div>

---

## Indicadores de Desempenho e Qualidade do Projeto

<div class="metric-grid" markdown>

<div class="metric-card success" markdown>
<div class="metric-value">0.00%</div>
<div class="metric-label">Falsos Positivos em Certidoes (Tolerancia Zero)</div>
</div>

<div class="metric-card info" markdown>
<div class="metric-value">100.0%</div>
<div class="metric-label">Acuracia no Benchmark de Harness Evals</div>
</div>

<div class="metric-card" markdown>
<div class="metric-value">8 Sprints</div>
<div class="metric-label">Cronograma Estruturado ate 07/12/2026</div>
</div>

<div class="metric-card warning" markdown>
<div class="metric-value">15 RFs</div>
<div class="metric-label">Requisitos Funcionais com Trilha Auditavel</div>
</div>

</div>

---

## O Ciclo de Processamento Documental

<div class="pipeline-strip" markdown>

<div class="pipeline-step">
  <span class="step-num">Passo 01</span>
  <span class="step-name">Ingestao S3</span>
</div>

<div class="pipeline-step">
  <span class="step-num">Passo 02</span>
  <span class="step-name">IDP & OCR</span>
</div>

<div class="pipeline-step">
  <span class="step-num">Passo 03</span>
  <span class="step-name">Schemas JSON</span>
</div>

<div class="pipeline-step">
  <span class="step-num">Passo 04</span>
  <span class="step-name">Regras BNDES</span>
</div>

<div class="pipeline-step">
  <span class="step-num">Passo 05</span>
  <span class="step-name">Maker-Checker</span>
</div>

<div class="pipeline-step">
  <span class="step-num">Passo 06</span>
  <span class="step-name">Laudo & Auditoria</span>
</div>

</div>

---

## Pilares Tecnologicos da Solucao

<div class="bento-grid" markdown>

<div class="bento-card span-2" markdown>
<div>
  <span class="bento-tag">Engenharia de Documentos</span>
  <h3>Pipeline IDP Hibrido e OCR Tesseract 5</h3>
  <p>Extracao vetorial nativa de alta velocidade com fallback automatico para OCR Tesseract 5 em paginas digitalizadas. Pre-processamento adaptativo de imagem e deteccao de tabelas complexas com calibracao para o idioma portugues.</p>
</div>
<a href="engineering/idp-pipeline/" class="bento-meta">Conhecer o Pipeline de Extracao &rarr;</a>
</div>

<div class="bento-card" markdown>
<div>
  <span class="bento-tag">Harness de Inteligencia Artificial</span>
  <h3>Padrao Maker-Checker Algoritmico</h3>
  <p>Auditoria semantica cruzada: o agente propositor aponta a evidencia textual e o auditor algoritmico valida a correspondencia literal exata no documento original antes da emissao do laudo.</p>
</div>
<a href="planning/harness-engineering/" class="bento-meta">Entender o Maker-Checker &rarr;</a>
</div>

<div class="bento-card" markdown>
<div>
  <span class="bento-tag">Determinismo Normativo</span>
  <h3>Motor Declarativo de Regras</h3>
  <p>Checklists e restricoes de negocio desacoplados em esquemas JSON Schema versionados. Validacao temporal estrita de certidoes (CND, FGTS, CNDT, Falencia) com tolerancia zero a ambiguidades.</p>
</div>
<a href="engineering/rules-engine/" class="bento-meta">Explorar Motor de Regras &rarr;</a>
</div>

<div class="bento-card span-2" markdown>
<div>
  <span class="bento-tag">Governanca e Compliance Publico</span>
  <h3>Trilha de Auditoria Imutavel e Conformidade LGPD</h3>
  <p>Registro transacional imutavel (append-only) de cada deliberacao tecnica com hash criptografico SHA-256 do arquivo original, timestamp UTC e parecer circunstanciado para orgaos de fiscalizacao (TCU e CGU).</p>
</div>
<a href="planning/governance-security/" class="bento-meta">Ver Diretrizes de Governanca &rarr;</a>
</div>

</div>

---

## Navegacao Estruturada do Portal

<div class="grid cards" markdown>

- ### [Planejamento Estrategico](planning/index.md)
    Entendimento do edital, requisitos funcionais RF01-RF15, roadmap de 8 sprints e Definition of Done.
    - [Visao Geral do Planejamento](planning/index.md)
    - [Requisitos Funcionais e RNF](planning/requirements.md)
    - [Arquitetura e Segregacao Regras/IA](planning/architecture-design.md)
    - [Cronograma de Sprints](planning/sprints-roadmap.md)
    - [Seguranca e LGPD](planning/governance-security.md)
    - [Harness Engineering](planning/harness-engineering.md)

- ### [Arquitetura e Decisoes (ADRs)](architecture/overview.md)
    Topologia de servicos conteinerizados, diagramas de fluxo de dados e registros formais de decisao.
    - [Visao Geral da Arquitetura](architecture/overview.md)
    - [Indice Central de ADRs](architecture/adr-index.md)
    - [ADR-001: Monorepo Modular](architecture/adr-001-monorepo-modular.md)
    - [ADR-002: Adoção do Astral uv](architecture/adr-002-astral-uv-toolchain.md)
    - [ADR-003: React SPA vs Next.js](architecture/adr-003-spa-vs-nextjs.md)

- ### [Desafio e Normativos BNDES](bndes/compliance-matrix.md)
    Mapeamento dos requisitos da Consulta Publica no 01/2025 e especificacao tecnica das certidoes.
    - [Matriz de Aderencia ao Edital](bndes/compliance-matrix.md)
    - [Tipologias de Documentos do BNDES](bndes/document-types.md)

- ### [Desenvolvimento e Operacao Local](development/quickstart.md)
    Manuais praticos de configuracao rapida com Make, Docker e Astral uv, alem de contratos OpenAPI.
    - [Guia de Inicio Rapido (Quickstart)](development/quickstart.md)
    - [Referencia da API REST (OpenAPI)](development/api-reference.md)
    - [Quality Gates e Protocolos de Teste](development/quality-gates.md)

</div>

---

## Acesso Operacional aos Servicos Locais

| Servico | URL Host | Finalidade Operacional |
| :--- | :--- | :--- |
| **Frontend SPA** | [http://localhost:5173](http://localhost:5173) | Cockpit do analista de credito para revisao e envio de certidoes. |
| **Backend API (Swagger Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Catalogo interativo OpenAPI / Swagger das rotas da API. |
| **Healthcheck da API** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Diagnostico em tempo real do PostgreSQL, Redis e MinIO. |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | Interface web do S3 Object Storage para inspecao de PDFs originais. |
| **Documentacao MkDocs** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | Servidor local com recarregamento a quente via `make docs`. |

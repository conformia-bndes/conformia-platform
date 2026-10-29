---
hide:
  - navigation
  - toc
---

<div class="apple-landing-wrap">

<div class="apple-hero">
  <span class="apple-eyebrow">Consulta Pública BNDES nº 01/2025</span>
  <h1 class="apple-title">Conform.IA BNDES</h1>
  <p class="apple-headline">Processamento Inteligente de Documentos com Trilha de Auditoria</p>
  <p class="apple-subheadline">
    Verificação automatizada de certidões cadastrais, fiscais, trabalhistas e regulatórias para operações de crédito do BNDES, com evidência rastreável e revisão humana quando há dúvida.
  </p>
  <div class="apple-cta-group">
    <a href="development/quickstart/" class="apple-btn-primary">Começar pelo Início Rápido</a>
    <a href="planning/DELIVERY_PLAN_2026_12_05/" class="apple-btn-secondary">Ver Plano de Entrega</a>
  </div>
</div>

<div class="apple-stat-strip">
  <div class="apple-stat-item">
    <div class="apple-stat-number">0</div>
    <div class="apple-stat-label">Falsos positivos no benchmark de regras (bloqueante no CI)</div>
  </div>
  <div class="apple-stat-item">
    <div class="apple-stat-number apple-stat-number--text">Fail-closed</div>
    <div class="apple-stat-label">Falha de IA ou dado ausente vira revisão manual</div>
  </div>
  <div class="apple-stat-item">
    <div class="apple-stat-number">05/12/2026</div>
    <div class="apple-stat-label">Entrega do MVP (milestones M1 a M6)</div>
  </div>
  <div class="apple-stat-item">
    <div class="apple-stat-number">15 RFs</div>
    <div class="apple-stat-label">Requisitos funcionais mapeados</div>
  </div>
</div>

<div class="apple-section-header">
  <h2 class="apple-section-title">Pilares Fundamentais da Solução</h2>
  <p class="apple-section-desc">Regras determinísticas decidem, a IA só atua sob verificação e toda decisão deixa rastro.</p>
</div>

<div class="apple-grid-3">
  <div class="apple-card">
    <div>
      <span class="apple-card-tag">Pipeline IDP</span>
      <h3 class="apple-card-title">Extração Híbrida e OCR</h3>
      <p class="apple-card-desc">
        Texto nativo do PDF com pdfplumber e OCR Tesseract em português nas páginas digitalizadas, com página e trecho de cada evidência.
      </p>
    </div>
    <a href="engineering/idp-pipeline/" class="apple-card-link">Explorar Pipeline IDP &rarr;</a>
  </div>

  <div class="apple-card">
    <div>
      <span class="apple-card-tag">Harness de IA</span>
      <h3 class="apple-card-title">Maker-Checker com Citação Verificada</h3>
      <p class="apple-card-desc">
        Um modelo propõe a avaliação com citação literal, outro audita, e a citação precisa existir no documento. Qualquer falha encaminha para revisão humana.
      </p>
    </div>
    <a href="engineering/maker-checker/" class="apple-card-link">Entender Maker-Checker &rarr;</a>
  </div>

  <div class="apple-card">
    <div>
      <span class="apple-card-tag">Auditoria</span>
      <h3 class="apple-card-title">Trilha de Auditoria</h3>
      <p class="apple-card-desc">
        Cada avaliação é registrada junto com o laudo, com o SHA-256 do documento, e a decisão humana fica em uma trilha somente de inserção, com segregação de funções.
      </p>
    </div>
    <a href="planning/governance-security/" class="apple-card-link">Ver Segurança e Auditoria &rarr;</a>
  </div>
</div>

<div class="apple-section-header">
  <h2 class="apple-section-title">Navegação do Portal de Engenharia</h2>
  <p class="apple-section-desc">Escolha por onde começar conforme o seu papel no projeto.</p>
</div>

<div class="apple-nav-grid">
  <a href="planning/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Estratégia</span>
      <h4 class="apple-nav-title">Planejamento e Requisitos</h4>
      <p class="apple-nav-text">Entendimento do edital, requisitos RF01 a RF15 e rastreabilidade com os testes.</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>

  <a href="architecture/overview/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Engenharia</span>
      <h4 class="apple-nav-title">Arquitetura e Decisões (ADRs)</h4>
      <p class="apple-nav-text">Serviços, fluxo de processamento, modelo de dados e decisões técnicas (ADR-001 a ADR-003).</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>

  <a href="bndes/compliance-matrix/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Normativos</span>
      <h4 class="apple-nav-title">Desafio e Certidões BNDES</h4>
      <p class="apple-nav-text">Mapeamento dos requisitos da Consulta Pública nº 01/2025 e das tipologias de certidões.</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>

  <a href="development/quickstart/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Operação</span>
      <h4 class="apple-nav-title">Desenvolvimento e APIs</h4>
      <p class="apple-nav-text">Início rápido com Docker e uv, referência da API REST e quality gates.</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>
</div>

<div class="apple-section-header">
  <h2 class="apple-section-title">Serviços e Portas em Ambiente Local</h2>
  <p class="apple-section-desc">Endereços disponíveis após <code>make up</code>.</p>
</div>

<div class="apple-table-wrap">
  <table class="apple-table">
    <thead>
      <tr>
        <th>Serviço</th>
        <th>URL Local</th>
        <th>Finalidade Operacional</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Frontend SPA</strong></td>
        <td><a href="http://localhost:5173" target="_blank" rel="noopener noreferrer">http://localhost:5173</a></td>
        <td>Painel do analista: upload, laudo e revisão humana.</td>
      </tr>
      <tr>
        <td><strong>Backend API (Swagger)</strong></td>
        <td><a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">http://localhost:8000/docs</a></td>
        <td>Catálogo interativo OpenAPI das rotas da API.</td>
      </tr>
      <tr>
        <td><strong>Healthcheck da API</strong></td>
        <td><a href="http://localhost:8000/api/v1/health" target="_blank" rel="noopener noreferrer">http://localhost:8000/api/v1/health</a></td>
        <td>Estado do PostgreSQL, do Redis e do MinIO.</td>
      </tr>
      <tr>
        <td><strong>MinIO Console</strong></td>
        <td><a href="http://localhost:9001" target="_blank" rel="noopener noreferrer">http://localhost:9001</a></td>
        <td>Console do armazenamento de objetos (PDFs originais).</td>
      </tr>
      <tr>
        <td><strong>Documentação MkDocs</strong></td>
        <td><a href="http://127.0.0.1:8001" target="_blank" rel="noopener noreferrer">http://127.0.0.1:8001</a></td>
        <td>Esta documentação, servida localmente por <code>make docs</code>.</td>
      </tr>
    </tbody>
  </table>
</div>

</div>

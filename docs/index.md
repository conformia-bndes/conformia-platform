---
hide:
  - navigation
  - toc
---

<div class="apple-landing-wrap">

<div class="apple-hero">
  <span class="apple-eyebrow">Consulta Pública BNDES nº 01/2025</span>
  <h1 class="apple-title">Conform.IA BNDES</h1>
  <p class="apple-headline">Processamento Inteligente de Documentos e Auditoria Imutável</p>
  <p class="apple-subheadline">
    Plataforma de alta precisão pericial para verificação automatizada de conformidade cadastral, fiscal, trabalhista e regulatória em operações de crédito e investimentos no BNDES.
  </p>
  <div class="apple-cta-group">
    <a href="development/quickstart/" class="apple-btn-primary">Começar pelo Início Rápido</a>
    <a href="planning/DELIVERY_PLAN_2026_12_05/" class="apple-btn-secondary">Ver Plano de Entrega</a>
  </div>
</div>

<div class="apple-stat-strip">
  <div class="apple-stat-item">
    <div class="apple-stat-number">0</div>
    <div class="apple-stat-label">Falsos Positivos no Benchmark de Regras</div>
  </div>
  <div class="apple-stat-item">
    <div class="apple-stat-number">Fail-closed</div>
    <div class="apple-stat-label">Falha de IA ou Dado Ausente Vira Revisão Manual</div>
  </div>
  <div class="apple-stat-item">
    <div class="apple-stat-number">05/12/2026</div>
    <div class="apple-stat-label">Entrega do MVP (Milestones M1 a M6)</div>
  </div>
  <div class="apple-stat-item">
    <div class="apple-stat-number">15 RFs</div>
    <div class="apple-stat-label">Requisitos Funcionais Mapeados</div>
  </div>
</div>

<div class="apple-section-header">
  <h2 class="apple-section-title">Pilares Fundamentais da Solução</h2>
  <p class="apple-section-desc">Arquitetura concebida para atender aos requisitos de conformidade com precisão pericial e rastreabilidade total.</p>
</div>

<div class="apple-grid-3">
  <div class="apple-card">
    <div>
      <span class="apple-card-tag">Pipeline IDP</span>
      <h3 class="apple-card-title">Extração Híbrida e OCR</h3>
      <p class="apple-card-desc">
        Extração vetorial nativa de texto com fallback automático para OCR Tesseract 5 em certidões digitalizadas, com pre-processamento adaptativo e calibração para o idioma português.
      </p>
    </div>
    <a href="engineering/idp-pipeline/" class="apple-card-link">Explorar Pipeline IDP &rarr;</a>
  </div>

  <div class="apple-card">
    <div>
      <span class="apple-card-tag">Harness de IA</span>
      <h3 class="apple-card-title">Maker-Checker Algoritmico</h3>
      <p class="apple-card-desc">
        O modelo propositor formula hipóteses com citação literal compulsoria. O auditor algoritmico valida a correspondência textual antes de admitir qualquer laudo, eliminando alucinações.
      </p>
    </div>
    <a href="planning/harness-engineering/" class="apple-card-link">Entender Maker-Checker &rarr;</a>
  </div>

  <div class="apple-card">
    <div>
      <span class="apple-card-tag">Governança</span>
      <h3 class="apple-card-title">Auditoria Imutável e LGPD</h3>
      <p class="apple-card-desc">
        Registro transacional append-only de cada análise com hash SHA-256 do documento original, carimbo temporal UTC e parecer pericial estruturado para o TCU e a CGU.
      </p>
    </div>
    <a href="planning/governance-security/" class="apple-card-link">Ver Diretrizes de Governança &rarr;</a>
  </div>
</div>

<div class="apple-section-header">
  <h2 class="apple-section-title">Navegação do Portal de Engenharia</h2>
  <p class="apple-section-desc">Acesso estruturado as dimensões estratégica, arquitetural, normativa e operacional da plataforma.</p>
</div>

<div class="apple-nav-grid">
  <a href="planning/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Estratégia</span>
      <h4 class="apple-nav-title">Planejamento e Requisitos</h4>
      <p class="apple-nav-text">Entendimento do edital, requisitos RF01 a RF15, matriz de dores operacionais e roadmap de sprints.</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>

  <a href="architecture/overview/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Engenharia</span>
      <h4 class="apple-nav-title">Arquitetura e Decisões (ADRs)</h4>
      <p class="apple-nav-text">Topologia de serviços conteinerizados, diagramas C4 e registros de decisão técnica (ADR-001 a ADR-003).</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>

  <a href="bndes/compliance-matrix/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Normativos</span>
      <h4 class="apple-nav-title">Desafio e Certidões BNDES</h4>
      <p class="apple-nav-text">Mapeamento dos requisitos da Consulta Publica no 01/2025 e especificação técnica das tipologias de certidões.</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>

  <a href="development/quickstart/" class="apple-nav-card">
    <div>
      <span class="apple-nav-category">Operação</span>
      <h4 class="apple-nav-title">Desenvolvimento e APIs</h4>
      <p class="apple-nav-text">Guia de inicio rápido com Docker e Astral uv, contratos OpenAPI (Swagger) e quality gates.</p>
    </div>
    <span class="apple-nav-arrow">&rarr;</span>
  </a>
</div>

<div class="apple-section-header">
  <h2 class="apple-section-title">Serviços e Portas em Ambiente Local</h2>
  <p class="apple-section-desc">Catalogo de serviços e endpoints para analistas e equipes de engenharia.</p>
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
        <td>Cockpit operacional do analista de crédito do BNDES.</td>
      </tr>
      <tr>
        <td><strong>Backend API (Swagger)</strong></td>
        <td><a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">http://localhost:8000/docs</a></td>
        <td>Catalogo interativo OpenAPI das rotas da API.</td>
      </tr>
      <tr>
        <td><strong>Healthcheck da API</strong></td>
        <td><a href="http://localhost:8000/api/v1/health" target="_blank" rel="noopener noreferrer">http://localhost:8000/api/v1/health</a></td>
        <td>Diagnóstico em tempo real do PostgreSQL, Redis e MinIO.</td>
      </tr>
      <tr>
        <td><strong>MinIO Console</strong></td>
        <td><a href="http://localhost:9001" target="_blank" rel="noopener noreferrer">http://localhost:9001</a></td>
        <td>Interface web do S3 Object Storage para armazenamento de PDFs.</td>
      </tr>
      <tr>
        <td><strong>Documentação MkDocs</strong></td>
        <td><a href="http://127.0.0.1:8000" target="_blank" rel="noopener noreferrer">http://127.0.0.1:8000</a></td>
        <td>Servidor local com recarregamento a quente via <code>make docs</code>.</td>
      </tr>
    </tbody>
  </table>
</div>

</div>

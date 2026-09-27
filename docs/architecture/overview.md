# Visão Geral da Arquitetura

O Conform.IA BNDES adota uma arquitetura modular baseada em microsserviços integrados em monorepo, projetada para desacoplamento de responsabilidades, alta disponibilidade e rastreabilidade total.

---

## Diagrama Estrutural do Sistema

```mermaid
flowchart TD
    subgraph Frontend["Camada de Apresentação"]
        SPA["React 18 SPA (Vite / TypeScript / Tailwind)"]
        UI_Upload["Modulo de Ingestao IDP"]
        UI_Checklist["Painel de Checklist BNDES"]
        UI_Audit["Trilha de Auditoria e Laudos"]
    end

    subgraph API_Gateway["Camada de API e Roteamento"]
        FastAPI["FastAPI 0.110+ (Uvicorn)"]
        CORS["Middleware de CORS Parametrizado"]
        ExceptionH["Tratamento Global de Excecoes"]
        Route_Health["/api/v1/health"]
        Route_Docs["/api/v1/documents"]
        Route_Comp["/api/v1/compliance"]
    end

    subgraph Worker_Tier["Processamento Assíncrono e IA"]
        CeleryWorker["Celery 5 Worker"]
        IDPExtractor["Extrator Hibrido (pdfplumber / Tesseract)"]
        RulesEngine["Motor de Regras (rules/schemas)"]
        MakerChecker["Validador Maker-Checker (LLM Harness)"]
    end

    subgraph Persistence_Tier["Camada de Dados e Armazenamento"]
        Postgres[("PostgreSQL 16\n(Documentos, Checks e Logs de Auditoria)")]
        Redis[("Redis 7\n(Broker Celery e Cache)")]
        MinIO[("MinIO S3\n(Bucket de Documentos PDF)")]
    end

    SPA -->|HTTPS / JSON| FastAPI
    FastAPI --> Route_Health & Route_Docs & Route_Comp
    Route_Docs -->|Persistencia Binaria| MinIO
    Route_Docs -->|Disparo de Tarefas| Redis
    Redis --> CeleryWorker
    CeleryWorker --> IDPExtractor --> RulesEngine --> MakerChecker
    RulesEngine -->|Gravacao de Laudo| Postgres
    MakerChecker -->|Trilha Imutavel| Postgres
    Route_Comp -->|Consulta de Laudo| Postgres
```

---

## Componentes da Solução

### 1. Camada de Apresentação (Frontend)

- **Tecnologias**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Axios.
- **Responsabilidade**: Fornecer interface reativa para analistas de crédito e operadores do BNDES, permitindo o carregamento de PDFs, visualização imediata de pendências e consulta do histórico de auditoria.

### 2. Camada de API (Backend Core)

- **Tecnologias**: Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pydantic-Settings.
- **Responsabilidade**: Exposicao de endpoints RESTful seguros, validacao estrita de contratos de entrada, gestao de conexoes e persistencia de estado.

### 3. Camada de Processamento Assíncrono (Worker)

- **Tecnologias**: Celery, Redis, pdfplumber, pytesseract, Poppler-utils.
- **Responsabilidade**: Processamento de arquivos pesados, OCR em paginas digitalizadas e execucao de regras de conformidade sem bloqueio das requisicoes HTTP da API.

### 4. Camada de Persistência

- **PostgreSQL 16**: Armazena entidades estruturadas (`Document`, `ComplianceCheck`, `AuditLog`).
- **Redis 7**: Fila de mensagens para tarefas do Celery e cache de regras frequentes.
- **MinIO**: Object storage compativel com a API S3 para persistencia duravel dos arquivos PDF originais.

---

## Fluxo de Processamento de Documentos

1. **Ingestão**: O usuário envia um PDF através da interface ou de uma chamada de API (`POST /api/v1/documents/upload`).
2. **Armazenamento**: O arquivo é salvo no volume seguro, e um registro inicial é criado no banco com status `PROCESSING`.
3. **Extração IDP**: O extrator processa as páginas nativas. Se a densidade textual for inferior ao limiar mínimo, o OCR via Tesseract é acionado.
4. **Avaliação de Conformidade**: O motor de regras compara o texto extraído com o catálogo normativo (BNDES 01/2025). Regras semânticas são validadas pelo ciclo Maker-Checker.
5. **Auditoria**: O resultado é consolidado, salvo no banco e registrado na tabela de auditoria (`audit_logs`).

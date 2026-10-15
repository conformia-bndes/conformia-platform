# Referência da API REST (OpenAPI / Swagger)

A API do Conform.IA BNDES segue padrões RESTful, com comunicação via JSON e documentação interativa gerada automaticamente pelo FastAPI.

- **Swagger UI Interativo**: `http://localhost:8000/docs`
- **ReDoc Alternativo**: `http://localhost:8000/redoc`
- **Prefixo Oficial das Rotas**: `/api/v1`

---

## 1. Módulo de Saúde do Sistema (`/health`)

### `GET /api/v1/health`

Retorna o diagnóstico operacional de todos os serviços da infraestrutura.

**Resposta de Sucesso (`200 OK`):**

```json
{
  "status": "healthy",
  "app_name": "Conform.IA BNDES Platform",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-27T03:47:03.250864",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "minio": "ready"
  }
}
```

---

## 2. Módulo de Documentos e IDP (`/documents`)

### `POST /api/v1/documents/upload`

Recebe um arquivo PDF para ingestão, executa validação de magic bytes (`%PDF-`), grava no MinIO S3 e dispara extração textual vetorial/OCR.

- **Content-Type**: `multipart/form-data`
- **Parametros**:
  - `file`: Arquivo binário PDF (máximo 50 MB).
  - `async_process` (query param, boolean, default: `false`): Executar via Celery background worker.

**Resposta (`201 Created`):**

```json
{
  "id": "doc-550e8400-e29b-41d4-a716-446655440000",
  "filename": "cnd_receita_federal.pdf",
  "status": "COMPLETED",
  "file_size": 245760,
  "total_pages": 1,
  "created_at": "2026-09-27T03:50:00Z"
}
```

### `GET /api/v1/documents`

Lista paginada de documentos processados na plataforma.

- **Query Params**: `skip` (default: 0), `limit` (default: 50).

### `GET /api/v1/documents/{document_id}`

Recupera os metadados cadastrais extraídos e o preview textual do documento.

### `GET /api/v1/documents/{document_id}/processing`

Consulta o estado atual do processamento e o resultado detalhado da extração IDP por identificador único (UUID).
Também acessível através dos aliases `/status` e `/extraction`.

- **Parâmetros de Rota**:
  - `document_id`: UUID do documento submetido.

#### Resposta de Sucesso (`200 OK` - Status: `COMPLETED`)

Retorna quando o processamento IDP foi concluído, fornecendo campos tipados e evidências textuais referenciadas por página:

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "cnd_receita_federal.pdf",
  "status": "COMPLETED",
  "progress": 1.0,
  "message": "Processamento e extracao concluidos com sucesso.",
  "extraction": {
    "document_type": "CND_FEDERAL",
    "fields": {
      "cnpj": {
        "name": "cnpj",
        "value": "12.345.678/0001-90",
        "raw_value": "12.345.678/0001-90",
        "confidence": 1.0,
        "evidence": {
          "text": "CNPJ: 12.345.678/0001-90",
          "page": 1,
          "confidence": 1.0,
          "bounding_box": null
        }
      },
      "data_validade": {
        "name": "data_validade",
        "value": "2026-12-31",
        "raw_value": "31/12/2026",
        "confidence": 1.0,
        "evidence": {
          "text": "Valida ate: 31/12/2026",
          "page": 1,
          "confidence": 1.0,
          "bounding_box": null
        }
      }
    },
    "evidences": [
      {
        "text": "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS",
        "page": 1,
        "confidence": 1.0,
        "bounding_box": null
      },
      {
        "text": "CNPJ: 12.345.678/0001-90",
        "page": 1,
        "confidence": 1.0,
        "bounding_box": null
      }
    ],
    "total_pages": 1,
    "tables": [],
    "full_text_preview": "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA..."
  },
  "error": null,
  "created_at": "2026-10-12T19:00:00Z",
  "updated_at": "2026-10-12T19:00:05Z"
}
```

#### Resposta em Processamento (`200 OK` - Status: `PROCESSING` ou `PENDING`)

Retorna enquanto o documento está na fila de extração ou sendo processado em background:

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "certidao_fgts_crf.pdf",
  "status": "PROCESSING",
  "progress": 0.5,
  "message": "Documento em processamento na esteira de extracao IDP e OCR.",
  "extraction": null,
  "error": null,
  "created_at": "2026-10-12T19:00:00Z",
  "updated_at": "2026-10-12T19:00:02Z"
}
```

#### Resposta em Caso de Falha (`200 OK` - Status: `EXTRACTION_FAILED` ou `FAILED`)

Retorna estrutura detalhada do erro para análise e rastreabilidade:

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "arquivo_danificado.pdf",
  "status": "EXTRACTION_FAILED",
  "progress": 0.0,
  "message": "Falha durante o processamento documental.",
  "extraction": null,
  "error": {
    "code": "EXTRACTION_FAILED",
    "message": "Erro ao extrair conteudo do documento: Arquivo corrompido.",
    "details": {
      "stage": "pdfplumber_parsing",
      "error_class": "RuntimeError"
    },
    "timestamp": "2026-10-12T19:00:03Z"
  },
  "created_at": "2026-10-12T19:00:00Z",
  "updated_at": "2026-10-12T19:00:03Z"
}
```

#### Resposta Não Encontrado (`404 Not Found`)

```json
{
  "detail": "Documento nao encontrado."
}
```

---

## 3. Módulo de Conformidade e Regras (`/compliance`)

### `POST /api/v1/compliance/verify/{document_id}`

Executa a avaliação automatizada das regras do checklist BNDES contra o documento ingerido.

**Resposta (`200 OK`):**

```json
{
  "report_id": "rep-7f8e9a-2026",
  "document_id": "doc-550e8400-e29b-41d4-a716-446655440000",
  "overall_status": "COMPLIANT",
  "total_checks": 5,
  "compliant_count": 5,
  "non_compliant_count": 0,
  "manual_review_count": 0,
  "evaluated_at": "2026-09-27T03:51:00Z"
}
```

### `GET /api/v1/compliance/rules`

Retorna todas as regras ativas configuradas no catálogo declarativo JSON Schema do BNDES.

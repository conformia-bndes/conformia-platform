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

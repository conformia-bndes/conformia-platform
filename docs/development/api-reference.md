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
Somente as regras da tipologia detectada (`document_type`) são avaliadas; as demais ficam
`NOT_APPLICABLE`. Tipologia não identificada resulta em `MANUAL_REVIEW_REQUIRED` sem regras
avaliadas. O laudo vigente é substituído e cada execução é registrada na trilha de auditoria.

**Resposta (`200 OK`):**

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_filename": "cnd_receita_federal.pdf",
  "document_type": "CND_FEDERAL",
  "overall_status": "COMPLIANT",
  "compliance_score": 1.0,
  "total_rules": 6,
  "evaluated_rules": 1,
  "compliant_rules": 1,
  "checks": [
    {
      "rule_id": "RULE-BNDES-001",
      "rule_title": "Certidão Negativa de Débitos Federais e Dívida Ativa da União",
      "category": "FISCAL",
      "status": "COMPLIANT",
      "confidence_score": 1.0,
      "checker_type": "DETERMINISTIC",
      "findings": "Todos os criterios deterministicos de conformidade foram atendidos.",
      "evidence": {"matched_keywords": ["..."], "validity_date": "31/12/2026"}
    }
  ]
}
```

Status por regra: `COMPLIANT`, `NON_COMPLIANT`, `MANUAL_REVIEW_REQUIRED` (inclui certidão sem
data de validade legível e regra híbrida sem LLM disponível) e `NOT_APPLICABLE`. O
`compliance_score` considera apenas regras aplicáveis.

### `GET /api/v1/compliance/rules`

Retorna todas as regras ativas configuradas no catálogo declarativo JSON Schema do BNDES.

---

## 4. Revisão Humana Maker-Checker (`/compliance/reviews`)

Decisão humana sobre o laudo automatizado (RF09). Um analista propõe (Maker) e **outro**
analista confirma ou devolve (Checker). Os eventos são append-only e cada um gera um registro
na trilha de auditoria com o identificador do analista.

**Autenticação:** as operações de escrita exigem a chave pessoal de um usuário com perfil
`ANALISTA` em `X-API-Key` (ou `Authorization: Bearer`), em qualquer ambiente. A chave de
serviço (`API_KEY`) e o acesso anônimo de desenvolvimento não podem decidir. Perfis `AUDITOR`
e `ADMIN` apenas consultam.

A chave pessoal tem o formato `<user_id>:<segredo>`. O servidor guarda em `API_USERS` apenas o
hash PBKDF2-HMAC-SHA256 do segredo, com sal próprio (campo `key_hash`); gere a chave e a entrada
com `python backend/scripts/create_api_user.py <user_id> <perfil>`. O prefixo `user_id` limita a
verificação a um único hash por requisição.

| Método e rota | Função | Respostas de erro |
| :-- | :-- | :-- |
| `GET /api/v1/compliance/reviews/{document_id}` | Estado derivado e histórico | `404` documento |
| `POST /api/v1/compliance/reviews/{document_id}` | Propor `APPROVE`, `REJECT` ou `EXCEPTION` com `justification` (20 a 4000 caracteres) | `401`, `403` perfil, `404`, `409` sem laudo ou proposta pendente, `422` validação ou `APPROVE` de laudo `NON_COMPLIANT` |
| `POST /api/v1/compliance/reviews/{document_id}/{proposal_id}/confirm` | Confirmar proposta de outro analista (`comment`, 10 a 4000) | `403` autor da proposta, `404`, `409` já resolvida |
| `POST /api/v1/compliance/reviews/{document_id}/{proposal_id}/return` | Devolver proposta de outro analista | idem |

**Estados (`state`):** `NO_REVIEW`, `PENDING_CHECK`, `FINAL` (última resolução confirmou),
`RETURNED` (última proposta devolvida; nova proposta permitida). `final_decision` é a decisão
da proposta confirmada mais recente.

```bash
# Analista A propõe
curl -s -X POST http://localhost:8000/api/v1/compliance/reviews/<document_id> \
  -H "X-API-Key: <analista-a>:<segredo>" -H "Content-Type: application/json" \
  -d '{"decision": "APPROVE", "justification": "Validade e CNPJ conferidos contra o original."}'
# Analista B confirma
curl -s -X POST http://localhost:8000/api/v1/compliance/reviews/<document_id>/<proposal_id>/confirm \
  -H "X-API-Key: <analista-b>:<segredo>" -H "Content-Type: application/json" \
  -d '{"comment": "Conferido de forma independente."}'
```

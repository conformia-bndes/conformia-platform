# ADR-005: Autenticação por Chaves Pessoais PBKDF2, RBAC por Rota e Política da Chave de Serviço

## Metadados

- **Status**: Aprovado
- **Data**: 2026-11-27
- **Autores**: Conform.IA Engineering Team
- **Revisores**: `backend`, `maintainers`
- **Épico / Requisito**: Issue #163 (RF01, RF10, decisão D1)

---

## 1. Contexto e Declaração do Problema

O requisito **RF01** em [Requisitos de Negócio](../planning/requirements.md) previa originalmente autenticação por token JWT com perfis `Admin`, `Analista` e `Auditor`. Contudo, no ciclo do MVP não há provedor de identidade institucional (IdP / OIDC / Keycloak) provisionado, e a decisão **D1** (29/10/2026, registrada em [Plano de Entrega](../planning/DELIVERY_PLAN_2026_12_05.md)) definiu o uso de chaves de API pessoais mapeadas no servidor (`API_USERS`).

A auditoria de 23/11/2026 (achados `AUD-03` e `AUD-19a`, Issue `#163`) identificou duas lacunas que precisavam ser fechadas antes da entrega:

1. **Divergência formal com RF01**: a adoção de chaves pessoais precisava de registro arquitetural formal com análise de riscos e atualização explícita do critério de aceite do RF01 para o MVP.
2. **RBAC incompleto e executor genérico na trilha**: apenas as rotas de revisão humana (`POST /api/v1/compliance/reviews/*`) aplicavam `require_role`; rotas de escrita (`upload`, `verify`) aceitavam qualquer perfil (inclusive `AUDITOR`) e gravavam `performed_by` fixo (`"API_UPLOAD"`, `"HARNESS_RULES_ENGINE"`, `"CELERY_WORKER"`), prejudicando a rastreabilidade de RF10.

---

## 2. Opções Consideradas

### Opção 1: Implementar emissão/validação própria de JWT e tela de login no MVP

- _Vantagens_: adere literalmente à redação original do RF01.
- _Desvantagens_: exige tabela de usuários/senhas, fluxo de login/refresh/revogação, gestão de chaves de assinatura e alterações amplas na SPA durante o período de Code Freeze (`26/11` a `09/12`), sem resolver a integração real com o IdP corporativo do BNDES (que continuaria pendente para pós-MVP).

### Opção 2: Formalizar chaves de API pessoais PBKDF2-HMAC-SHA256 com RBAC por rota no MVP

- _Vantagens_: já integrada ao frontend (`ApiKeyModal`, armazenamento exclusivo em memória da aba), ao CLI de provisionamento (`backend/scripts/create_api_user.py`) e ao smoke test; permite impor RBAC estrito por rota e gravar o `user_id` real em toda a trilha de auditoria sem violar o Code Freeze.
- _Desvantagens_: não possui expiração automática (TTL) nem federação SSO; rotação e revogação dependem de atualização de `API_USERS` no ambiente do servidor.

---

## 3. Decisão Adotada

Adota-se a **Opção 2** para o escopo do MVP, atualizando formalmente o critério de aceite do **RF01** em [Requisitos de Negócio](../planning/requirements.md) e mantendo a migração para JWT/OIDC corporativo no roadmap pós-MVP.

### 3.1 Matriz de Permissões (RBAC por Rota)

| Rota | `ANALISTA` | `AUDITOR` | `ADMIN` | Chave de serviço (`API_KEY`) | Sem credencial (produção) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `GET /`, `GET /api/v1/health` | Público | Público | Público | Público | `200` |
| `GET /api/v1/documents*` (lista, detalhe, status, task) | Permitido | Permitido | Permitido | Permitido (automação) | `401` |
| `GET /api/v1/compliance/rules`, `/results/{id}`, `/reviews/{id}` | Permitido | Permitido | Permitido | Permitido (automação) | `401` |
| `GET /api/v1/compliance/audit-trail` | Permitido | Permitido | Permitido | Permitido (automação) | `401` |
| `POST /api/v1/documents/upload` | Permitido | **`403`** | Permitido | Permitido (smoke/CI) | `401` |
| `POST /api/v1/compliance/verify/{document_id}` | Permitido | **`403`** | Permitido | Permitido (automação) | `401` |
| `POST /api/v1/compliance/reviews/{document_id}` | Permitido (chave pessoal) | **`403`** | Permitido (chave pessoal) | **`401`** (proibida) | `401` |
| `POST /api/v1/compliance/reviews/{document_id}/{proposal_id}/confirm` | Permitido (2º ator) | **`403`** | Permitido (2º ator) | **`401`** (proibida) | `401` |
| `POST /api/v1/compliance/reviews/{document_id}/{proposal_id}/return` | Permitido (2º ator) | **`403`** | Permitido (2º ator) | **`401`** (proibida) | `401` |

### 3.2 Executor Real na Trilha de Auditoria (RF10)

- `DOCUMENT_UPLOADED`: grava `performed_by = principal.user_id` (e `actor_role` em `details`).
- `COMPLIANCE_EVALUATION` via API (`POST /verify/{id}`): grava `performed_by = principal.user_id`.
- `COMPLIANCE_EVALUATION` via worker Celery: propaga o `performed_by` registrado no evento `DOCUMENT_UPLOADED` do mesmo documento e marca `details.trigger = "CELERY_WORKER"`, mantendo fallback para `"CELERY_WORKER"` apenas quando o documento não possui evento de upload prévio.
- `REVIEW_PROPOSED`, `REVIEW_CONFIRMED`, `REVIEW_RETURNED`: gravam o `actor_id` da chave pessoal com segregação obrigatória de funções.

### 3.3 Política da Chave de Serviço (`API_KEY`)

- Destinada exclusivamente à automação operacional controlada (smoke test, testes de resiliência, carga e contrato no CI).
- Nunca é aceita em decisões humanas (`POST /api/v1/compliance/reviews/*`), retornando `HTTP 401`.
- Toda ação executada com `API_KEY` fica marcada na trilha com `performed_by = "service"` e `actor_role = "SERVICE"`.
- O opt-in `ALLOW_ANONYMOUS_ACCESS=true` é permitido apenas em `development`/`test` e bloqueado na inicialização quando `ENVIRONMENT=production`.

---

## 4. Análise de Riscos e Mitigações (Chaves Pessoais)

| Risco | Impacto | Mitigação no MVP | Evolução Pós-MVP |
| :--- | :--- | :--- | :--- |
| **Vazamento de chave pessoal** | Alto | Servidor armazena apenas hash `PBKDF2-HMAC-SHA256` (≥ 100 mil iterações, sal aleatório de 128 bits); frontend guarda a chave somente em memória da aba (nunca em `localStorage`/`sessionStorage`); logs e auditoria nunca gravam o segredo. | Tokens de curta duração (JWT/OIDC). |
| **Ausência de expiração automática (TTL)** | Médio | Inventário enxuto de contas de demonstração; rotação manual recomendada antes de cada janela operacional. | Expiração curta (15–60 min) emitida pelo IdP. |
| **Rotação e revogação** | Médio | Revogação imediata removendo a entrada de `API_USERS` e reiniciando o backend; novas chaves geradas com `backend/scripts/create_api_user.py` (arquivo `<user_id>.key` fora do terminal). | Revogação centralizada no IdP / JWKS. |
| **Uso indevido da chave de serviço** | Alto | Recusada (`401`) em todas as operações de revisão humana; auditada como `performed_by = "service"`. | Identidade de carga de trabalho (OIDC / mTLS). |

---

## 5. Diretrizes de Implementação e Validação

- Centralizar a resolução de identidade e RBAC em `backend/app/core/security.py` (`authenticate_principal`, `require_access`, `require_role`, `require_read_access`, `require_write_access`, `require_audit_access`).
- Garantir cobertura automatizada `rota × perfil` em `backend/tests/test_api_authentication.py` descobrindo dinamicamente todas as rotas registradas no contrato OpenAPI (mais rotas ocultas).

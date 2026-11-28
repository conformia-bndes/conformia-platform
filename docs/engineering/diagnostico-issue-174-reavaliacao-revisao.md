# Diagnóstico Técnico — Issue #174 (`AUD-14`): Reavaliação durante Revisão Humana

- **Data:** 27/11/2026
- **Issue:** `#174` (*Investigar: reavaliação do laudo durante revisão humana pendente ou finalizada*)
- **Resultado da investigação:** **REPRODUZIDO** (confirmado em código e por dois testes automatizados em `backend/tests/test_reviews.py`).

---

## 1. Evidência no Código e Reprodução Automatizada

1. **Origem da falha (`Fact`):**
   - `POST /api/v1/compliance/verify/{document_id}` (`backend/app/api/v1/endpoints/compliance.py`) chama `evaluate_and_persist` (`backend/app/services/compliance_service.py`), que executa `db.query(ComplianceCheck).filter(ComplianceCheck.document_id == doc.id).delete()` e persiste novas linhas em `compliance_checks` **sem consultar `review_events`**.
   - `resolve_proposal` (`backend/app/services/review_service.py`) copia `report_status=proposal.report_status` da proposta original sem comparar com o laudo atual em `compliance_checks`.
   - O mesmo pode ocorrer quando o tempo avança (uma certidão que era `COMPLIANT` no dia da proposta vence antes da confirmação e alguém reexecuta `/verify/{id}` ou quando o checklist de regras é atualizado).
2. **Testes reproduzíveis adicionados em `backend/tests/test_reviews.py`:**
   - `test_issue_174_reverify_during_pending_review_reproduces_divergence`
   - `test_issue_174_reverify_after_final_review_reproduces_divergence`
   - Execução: `uv run --frozen pytest backend/tests/test_reviews.py backend/tests/test_compliance.py -q`

---

## 2. Análise de Riscos

| Cenário | Comportamento observado | Risco operacional / regulatório |
| :--- | :--- | :--- |
| **Revisão `PENDING_CHECK`** | `POST /verify/{id}` substitui `compliance_checks` para `NON_COMPLIANT`, mas `GET /reviews/{id}` permanece `PENDING_CHECK` com `report_status="COMPLIANT"`, e o 2º analista consegue confirmar `APPROVE`. | **Alto**: contorna indiretamente a regra de negócio de `review_service.py` segundo a qual um laudo `NON_COMPLIANT` só pode ser aceito via `EXCEPTION` motivada; cria laudo divergente da decisão humana. |
| **Revisão `FINAL`** | `POST /verify/{id}` altera o laudo vigente exibido em `GET /compliance/results/{id}` para `NON_COMPLIANT`, enquanto `GET /compliance/reviews/{id}` mantém `state="FINAL"` e `final_decision="APPROVE"`. | **Alto**: compromete a integridade da trilha pericial (`RF10`/`RNF03`), pois o laudo vigente deixa de corresponder ao objeto efetivamente deliberado pelos analistas. |

---

## 3. Comparação das Opções de Regra de Negócio

| Opção | Descrição | Vantagens | Trade-offs |
| :--- | :--- | :--- | :--- |
| **Opção A (Recomendada): Bloquear com `HTTP 409 Conflict`** | Impedir `POST /api/v1/compliance/verify/{id}` quando `get_review_state(db, doc.id)["state"] in ("PENDING_CHECK", "FINAL")`, retornando `409 Conflict` com mensagem clara. Permitir reavaliação somente quando `state in ("NO_REVIEW", "RETURNED")`. | Sem migration de esquema; compatível com triggers append-only (`#167`); preserva a invariante de que decisão `FINAL` refere-se ao laudo imutável; fácil de explicar ao analista na UI ("devolva a proposta pendente ou faça novo upload"). | Em documentos `FINAL`, exige novo upload de certidão para iniciar novo ciclo (o que já é o fluxo normativo esperado em crédito BNDES). |
| **Opção B: Invalidar proposta pendente via novo evento** | Ao reavaliar em `PENDING_CHECK`, gravar evento `INVALIDATED` / `SUPERSEDED` em `review_events` e bloquear apenas em `FINAL`. | Permite reavaliar sem intervenção do 2º analista em `PENDING_CHECK`. | Exige alteração de schema (`CHECK` constraint em `review_events.event_type` da `#167`), novos contratos de API e tratamento na SPA (`HumanReviewPanel.tsx`). |
| **Opção C: Versionar laudos (`report_version` / `evaluation_id`)** | Manter histórico de versões de `compliance_checks` vinculando cada `review_event` ao `evaluation_id` específico. | Rastreabilidade completa de múltiplas versões do laudo por documento. | Maior complexidade (nova tabela `compliance_reports`, migration, alteração em todos os endpoints de leitura/escrita e frontend); desproporcional ao MVP. |

**Recomendação técnica:** adotar a **Opção A (`HTTP 409 Conflict`)** em uma nova issue de correção, complementada por guarda equivalente em `resolve_proposal` verificando se o `report_status` atual de `compliance_checks` ainda corresponde a `proposal.report_status` (defesa em profundidade contra corrida concorrente).

---

## 4. Rascunhos Prontos para o GitHub

### 4.1 Rascunho de comentário para a Issue `#174`

```markdown
### Resultado da investigação (AUD-14) — REPRODUZIDO

A hipótese foi **reproduzida e confirmada** por análise do código (`compliance_service.py:56`,
`review_service.py:184-193`) e pelos testes automatizados adicionados em
`backend/tests/test_reviews.py`:
- `test_issue_174_reverify_during_pending_review_reproduces_divergence`
- `test_issue_174_reverify_after_final_review_reproduces_divergence`

**Impacto confirmado:** reexecutar `POST /api/v1/compliance/verify/{document_id}` enquanto existe
proposta `PENDING_CHECK` ou decisão `FINAL` substitui `compliance_checks` sem consultar
`review_events`. No cenário `PENDING_CHECK`, o 2º analista consegue inclusive confirmar `APPROVE`
sobre um laudo que já se tornou `NON_COMPLIANT` (contornando a exigência de `EXCEPTION`).

**Regra recomendada (Opção A — menor risco e aderente a RNF03):**
1. Bloquear `POST /api/v1/compliance/verify/{document_id}` com `HTTP 409 Conflict` quando o estado
   da revisão for `PENDING_CHECK` ou `FINAL` (permitir apenas em `NO_REVIEW` e `RETURNED`), com
   lock `with_for_update()` sobre `Document` para evitar corrida com `propose_decision`.
2. Em `resolve_proposal`, verificar se o `report_status` atual ainda coincide com
   `proposal.report_status` (defesa em profundidade).

Diagnóstico completo em `docs/engineering/diagnostico-issue-174-reavaliacao-revisao.md`.
```

### 4.2 Minuta da nova issue de correção

- **Título sugerido:** `Bloquear reavaliação do laudo (HTTP 409) durante revisão humana pendente ou finalizada`
- **Labels sugeridas:** `bug`, `P2`, `area: backend` *(elevar para `P1` se o Tech Lead considerar bloqueador de entrega)*
- **Milestone:** `M7 - Pos-entrega (endurecimento)`
- **Critérios de aceite verificáveis:**
  - [ ] `POST /api/v1/compliance/verify/{document_id}` retorna `HTTP 409 Conflict` quando `review_state in ("PENDING_CHECK", "FINAL")` e preserva `compliance_checks` inalterado.
  - [ ] `POST /api/v1/compliance/verify/{document_id}` continua retornando `HTTP 200` quando `review_state in ("NO_REVIEW", "RETURNED")`.
  - [ ] Serialização transacional (`with_for_update()`) evita corrida entre `/verify/{id}` e `POST /compliance/reviews/{id}`.
  - [ ] Testes automatizados em `backend/tests/test_reviews.py` e `backend/tests/test_compliance.py` substituem os testes de caracterização da `#174` e passam com `CI OK` verde.

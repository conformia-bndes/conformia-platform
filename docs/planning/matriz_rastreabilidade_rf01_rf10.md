# Matriz de Rastreabilidade — Requisitos RF01 a RF10 (MVP)

Este documento associa cada requisito funcional RF01–RF10 do MVP aos testes de
validação, estado atual no repositório e evidência de validação produzida pela
base de testes do fluxo inicial.

Fonte dos requisitos: `docs/planning/requirements.md` e
`docs/planning/project-plan.md`.

Base de testes: `backend/tests/test_initial_flow.py` e
`backend/tests/synthetic_pdfs.py`.

---

## Resumo da Matriz

| ID   | Requisito Funcional                     | Prioridade | Status no Repo | Teste de Validação                                    | Evidência de Validação                                                                 |
|:-----|:----------------------------------------|:-----------|:---------------|:------------------------------------------------------|:---------------------------------------------------------------------------------------|
| RF01 | Autenticacao e RBAC                     | Alta       | Planejado (S7) | — (nao coberto pelo fluxo inicial)                    | Nenhuma — requisito ainda nao implementado                                             |
| RF02 | Ingestao e Armazenamento                | Alta       | Implementado   | `test_upload_pdf_*_retorna_201`, `*_eh_rejeitado`     | HTTP 201 para PDF valido; HTTP 400 para extensao invalida / sem assinatura %PDF-       |
| RF03 | Pipeline IDP e OCR                      | Alta       | Implementado   | `test_processamento_pdf_valido_fluxo_completo`, `*_ilegivel_*` | STATUS=COMPLETED + documento_type=CND_FEDERAL; STATUS=EXTRACTION_FAILED para ilegível |
| RF04 | Estruturacao de Entidades               | Alta       | Implementado   | `test_processamento_pdf_valido_fluxo_completo`        | Campo CNPJ extraído com evidence.page=1 e value="12.345.678/0001-90"                   |
| RF05 | Checklist Declarativo                   | Alta       | Implementado   | — (nao coberto pelo fluxo inicial)                    | Regras carregadas de `rules/schemas/bndes_sample_checklist.json`                       |
| RF06 | Motor de Regras Determinístico          | Alta       | Implementado   | `test_processamento_certidao_vencida_nao_conforme`, `*_pendente_*` | RULE-BNDES-001 => NON_COMPLIANT (vencida/pendente), COMPLIANT (valida)                 |
| RF07 | Maker-Checker Assistido por IA          | Alta       | Implementado   | — (coberto por `test_maker_checker.py`)               | `MakerCheckerValidator` com fallback controlado sem API externa                        |
| RF08 | Exibicao de Evidencias                  | Alta       | Implementado   | `test_processamento_pdf_valido_fluxo_completo`        | ExtractedField com PageEvidence (texto + pagina + confianca) no GET /processing        |
| RF09 | Revisao Humana e Excecoes               | Alta       | Implementado   | — (nao coberto pelo fluxo inicial)                    | Endpoints de revisao humana e excecao motivada (fora do escopo do fluxo inicial)       |
| RF10 | Trilha de Auditoria Imutavel            | Alta       | Implementado   | — (coberto por `test_compliance.py`)                  | `GET /api/v1/compliance/audit-trail` retorna total >= 1 apos verificacao               |

---

## Detalhamento por Requisito

### RF01 — Autenticacao e RBAC
- **Descricao:** Suporte a autenticacao segura por token JWT com perfis segregados: `Admin`, `Analista`, `Auditor`.
- **Status no Repositorio:** Planejado (Sprint 7).
- **Cobertura na Base de Testes do Fluxo Inicial:** Nao coberto. O fluxo inicial de upload/processamento nao exige autenticacao (endpoints abertos em ambiente de teste/local).
- **Evidencia:** Nenhuma ainda. Pendente para Sprint 7.
- **Acao:** Incluir testes de auth/RBAC quando o requisito for implementado.

### RF02 — Ingestao e Armazenamento
- **Descricao:** Upload de arquivos PDF de até 50MB, validacao binária (`%PDF-`) e persistencia durável no MinIO S3.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:**
  - `test_upload_pdf_valido_retorna_201` — upload válido retorna 201.
  - `test_upload_pdf_vencido_retorna_201` — upload de certidao vencida aceito (regra temporal avaliada depois).
  - `test_upload_pdf_pendente_retorna_201` — upload de certidao com pendencia aceito.
  - `test_upload_arquivo_sem_extensao_pdf_eh_rejeitado` — extensão não-PDF rejeitada (400).
  - `test_upload_pdf_sem_assinatura_binaria_eh_rejeitado` — arquivo .pdf sem `%PDF-` rejeitado (400).
  - `test_upload_arquivo_binario_invalido_eh_rejeitado` — conteúdo binário invalido rejeitado (400).
- **Evidencia:** Resposta HTTP 201 com `id`, `filename`, `file_size`, `status` para arquivos válidos; HTTP 400 com `detail` contendo "PDF" ou "assinatura binaria" para arquivos invalidos.

### RF03 — Pipeline IDP e OCR
- **Descricao:** Extracao vetorial com fallback automático para OCR Tesseract em paginas digitalizadas (`CER <= 2.5%`).
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:**
  - `test_processamento_pdf_valido_fluxo_completo` — PDF nativo processado com sucesso (COMPLETED).
  - `test_processamento_pdf_ilegivel_extração_falha` — PDF digitalizado ilegível resulta em EXTRACTION_FAILED com erro estruturado.
- **Evidencia:** `status == "COMPLETED"` para PDF válido; `status == "EXTRACTION_FAILED"` + `error.message` contendo "sem texto legível" para PDF ilegível.

### RF04 — Estruturacao de Entidades
- **Descricao:** Reconhecimento de CNPJ, razões sociais, datas de emissao, datas de validade e codigos de controle.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:**
  - `test_processamento_pdf_valido_fluxo_completo` — CNPJ extraído com evidencia ancorada à pagina.
- **Evidencia:** `extraction.fields.cnpj.value == "12.345.678/0001-90"` e `extraction.fields.cnpj.evidence.page == 1`.

### RF05 — Checklist Declarativo
- **Descricao:** Carregamento dinamico de checklists versionados em JSON Schema sem necessidade de rebuild.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:** Nao coberto diretamente (as regras são carregadas pelo `RulesEngine` a partir de `rules/schemas/bndes_sample_checklist.json` ou regras padrao de contingencia).
- **Evidencia:** `RulesEngine()` instancia com sucesso e aplica regras `RULE-BNDES-001` a `RULE-BNDES-004`.

### RF06 — Motor de Regras Determinístico
- **Descricao:** Validacao booleana e temporal de certidoes (CND, CRF, CNDT, Falencia) com tolerancia zero a pendencias.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:**
  - `test_processamento_certidao_vencida_nao_conforme` — certidao vencida => `NON_COMPLIANT` com mensagem contendo "expirada".
  - `test_processamento_certidao_pendente_nao_conforme` — certidao com pendencia => `NON_COMPLIANT` com mensagem contendo "pendencia".
  - `test_processamento_pdf_valido_fluxo_completo` — certidao valida => `COMPLIANT`.
- **Evidencia:** `RULE-BNDES-001.status == "NON_COMPLIANT"` para vencida/pendente; `RULE-BNDES-001.status == "COMPLIANT"` para valida.

### RF07 — Maker-Checker Assistido por IA
- **Descricao:** Avaliacao semantica de cláusulas jurídicas com citacao literal compulsória de evidencia documental.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:** Nao coberto diretamente (coberto por `backend/tests/test_maker_checker.py`).
- **Evidencia:** `MakerCheckerValidator.evaluate_rule()` retorna `status` e `final_confidence` com fallback controlado.

### RF08 — Exibicao de Evidencias
- **Descricao:** Interface destacando o trecho exato e pagina do documento original que fundamentou a classificacao.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:**
  - `test_processamento_pdf_valido_fluxo_completo` — evidencias com página e texto no GET /processing.
- **Evidencia:** `extraction.evidences[]` contendo `text`, `page`, `confidence` para cada evidência extraída.

### RF09 — Revisao Humana e Excecoes
- **Descricao:** Fluxo operacional para analista aprovar, rejeitar ou deferir excecao justificada com parecer tecnico formal.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:** Nao coberto (fora do escopo do fluxo inicial de upload/processamento).
- **Evidencia:** Nenhuma nesta base de testes.

### RF10 — Trilha de Auditoria Imutavel
- **Descricao:** Gravacao transacional de todos os eventos com timestamp UTC, ID do executor, hash do arquivo e laudo.
- **Status no Repositorio:** Implementado.
- **Cobertura na Base de Testes do Fluxo Inicial:** Nao coberto diretamente (coberto por `backend/tests/test_compliance.py::test_api_verify_document_compliance_flow`).
- **Evidencia:** `GET /api/v1/compliance/audit-trail` retorna `total >= 1` apos verificacao de conformidade.

---

## Resultado Esperado por PDF de Referência

| Tipo         | Upload | Processamento | Regra RF06 | Erro Esperado                     |
|:-------------|:-------|:--------------|:-----------|:----------------------------------|
| valido       | 201    | COMPLETED     | COMPLIANT  | Nenhum                            |
| vencido      | 201    | COMPLETED     | NON_COMPLIANT | Contém "expirada"               |
| pendente     | 201    | COMPLETED     | NON_COMPLIANT | Contém "pendencia"              |
| ilegível     | 201    | EXTRACTION_FAILED | —      | Contém "sem texto legível"        |
| invalido     | 400    | —             | —          | Contém "assinatura binaria"       |

---

## Rastreabilidade Bidirecional

- **Requisito → Teste:** Cada RF acima possui ao menos um teste associado na base de testes do fluxo inicial (exceto RF01, RF05, RF07, RF09, RF10 que são cobertos por outros módulos de teste ou ainda não implementados).
- **Teste → Requisito:** Cada teste em `test_initial_flow.py` declara no docstring quais requisitos RF cobre (RF02, RF03, RF04, RF06).

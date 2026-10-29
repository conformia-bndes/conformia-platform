# Log de Defeitos — Fluxo Inicial (Upload, Processamento, Falha)

Registro de defeitos encontrados durante a criação e execução da base de testes
do fluxo inicial. Cada defeito inclui: identificador, título, requisitos afetados,
passos de reprodução, resultado esperado, resultado obtido, gravidade e status.

Formato de identificador: `DEF-FI-###` (Fluxo Inicial).

---

## Defeitos Registrados

| ID       | Título                                                  | Req. Afetados | Gravidade | Status     |
|:---------|:--------------------------------------------------------|:--------------|:----------|:-----------|
| DEF-FI-001 | RF01 (Autenticacao/RBAC) não implementado no fluxo de upload | RF01          | Alta      | Aberto     |
| DEF-FI-002 | PDF ilegível (digitalizado) não gera texto via OCR quando Tesseract está ausente | RF03          | Média     | Aberto     |
| DEF-FI-005 | Requisitos RF05, RF07, RF09, RF10 não cobertos pelo fluxo inicial de teste | RF05, RF07, RF09, RF10 | Baixa | Aberto     |

---

## Detalhamento dos Defeitos

### DEF-FI-001 — RF01 (Autenticacao/RBAC) não implementado no fluxo de upload

**Requisito Afetado:** RF01 — Autenticacao e RBAC  
**Status no Repositorio:** Planejado (Sprint 7) — ainda não implementado  
**Gravidade:** Alta  
**Status:** Aberto  

**Passos de Reprodução:**
1. Acessar o endpoint `POST /api/v1/documents/upload` sem qualquer token de autenticação.
2. Enviar um arquivo PDF válido.
3. Observar que o upload é aceito com status 201, sem exigência de JWT ou verificação de perfil (Admin/Analista/Auditor).

**Resultado Esperado:** O endpoint deve exigir autenticação via token JWT e validar o perfil do usuário antes de aceitar o upload.

**Resultado Obtido:** O upload é processado sem qualquer controle de acesso, permitindo ingestão de documentos por usuários não autenticados.

**Evidência:** Testes em `test_initial_flow.py` usam `TestClient` sem autenticação e recebem 201 com sucesso.

---

### DEF-FI-002 — PDF ilegível (digitalizado) não gera texto via OCR quando Tesseract está ausente

**Requisito Afetado:** RF03 — Pipeline IDP e OCR  
**Status no Repositorio:** Implementado  
**Gravidade:** Média  
**Status:** Aberto  

**Passos de Reprodução:**
1. Gerar um PDF digitalizado (apenas imagem, sem texto nativo) usando `build_scanned_pdf()`.
2. Enviar via `POST /api/v1/documents/upload?async_process=false`.
3. Consultar `GET /api/v1/documents/{id}/processing`.
4. Observar que o status é `EXTRACTION_FAILED` quando Tesseract não está instalado no ambiente.

**Resultado Esperado:** O sistema deve tentar OCR via Tesseract e, se disponível, extrair texto da imagem digitalizada.

**Resultado Obtido:** Quando Tesseract não está instalado, o extrator levanta `RuntimeError` com mensagem "OCR falhou na página" e o documento fica em `EXTRACTION_FAILED`.

**Evidência:** `test_processamento_pdf_ilegivel_extração_falha` valida que o erro é capturado e reportado com mensagem legível ("sem texto legível").

**Nota:** Este defeito é ambiental (dependência externa Tesseract não instalada), não um bug de código. O tratamento de erro está correto.

---

### DEF-FI-005 — Requisitos RF05, RF07, RF09, RF10 não cobertos pelo fluxo inicial de teste

**Requisitos Afetados:** RF05, RF07, RF09, RF10  
**Status no Repositorio:** Implementado  
**Gravidade:** Baixa  
**Status:** Aberto  

**Passos de Reprodução:**
1. Executar a bateria de testes do fluxo inicial (`test_initial_flow.py`).
2. Observar que nenhum teste exercita diretamente RF05 (Checklist Declarativo), RF07 (Maker-Checker), RF09 (Revisão Humana) ou RF10 (Trilha de Auditoria).
3. Verificar que esses requisitos são cobertos por outros módulos de teste (`test_compliance.py`, `test_maker_checker.py`), mas não pela base de testes do fluxo inicial.

**Resultado Esperado:** A base de testes do fluxo inicial deveria incluir cobertura para todos os requisitos RF01–RF10 do MVP.

**Resultado Obtido:** Apenas RF02, RF03, RF04 e RF06 são cobertos diretamente pelos testes do fluxo inicial. RF01 não está implementado. RF05, RF07, RF09, RF10 são cobertos por outros arquivos de teste.

**Evidência:** Matriz de rastreabilidade em `matriz_rastreabilidade_rf01_rf10.md` mostra as lacunas de cobertura.

**Acao Sugerida:** Adicionar testes específicos para RF05 (carregamento de checklist JSON Schema), RF07 (Maker-Checker via endpoint de verificação), RF09 (fluxo de revisão humana) e RF10 (consulta de trilha de auditoria) à base de testes do fluxo inicial.

---

## Resumo por Gravidade

| Gravidade | Quantidade | IDs                    |
|:----------|:-----------|:-----------------------|
| Alta      | 1          | DEF-FI-001             |
| Média     | 1          | DEF-FI-002             |
| Baixa     | 1          | DEF-FI-005             |
| **Total** | **3**      |                        |

---

## Critérios de Encerramento

Um defeito é considerado encerrado quando:
1. O código corrigido está implementado e commitado.
2. Um teste de regressão foi adicionado à base de testes do fluxo inicial.
3. O teste passa na execução da bateria completa (`pytest tests/`).

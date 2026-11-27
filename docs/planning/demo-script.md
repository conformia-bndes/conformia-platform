# Roteiro de Demonstração do MVP (Entrega 27/11/2026)

> A entrega, prevista originalmente para 05/12/2026, foi antecipada para 27/11/2026 (M6).

Este roteiro cobre a demonstração ponta a ponta do MVP (Issue `#63`), alinhado aos critérios de
aceite de `DELIVERY_PLAN_2026_12_05.md` (seção 5) e à integração de provedor LLM (`#129`).

---

## 1. Dados de Demonstração Fictícios e Seguros

Todos os arquivos abaixo ficam em `docs/samples/` e contêm apenas CNPJs, razões sociais e códigos
fictícios:

| Arquivo | Cenário / Tipologia | Resultado esperado no motor |
| :--- | :--- | :--- |
| `cnd_federal_ficticia_apresentacao.pdf` | CND Federal válida (até `15/05/2027`) | `COMPLIANT` (`RULE-BNDES-001`) |
| `cnd_federal_vencida.pdf` | CND Federal expirada (`10/07/2025`) | `NON_COMPLIANT` (`RULE-BNDES-001`) |
| `cnd_federal_sem_validade.pdf` | CND Federal sem data de validade legível | `MANUAL_REVIEW_REQUIRED` (`RULE-BNDES-001`) |
| `cnd_federal_positiva_reprovada.pdf` | CND Federal positiva com débitos | `NON_COMPLIANT` (`RULE-BNDES-001`) |
| `crf_fgts_conforme.pdf` | CRF FGTS regular (até `16/12/2026`) | `COMPLIANT` (`RULE-BNDES-002`) |
| `cndt_trabalhista_reprovada.pdf` | CNDT com débito ativo | `NON_COMPLIANT` (`RULE-BNDES-003`) |
| `licenca_ambiental_revisao_manual.pdf` | Licença Ambiental (2 páginas) | `MANUAL_REVIEW_REQUIRED` (sem LLM / ou avaliada com `#146` + LLM) |
| `cnd_federal_digitalizada_ocr.pdf` | CND Federal rasterizada (200 DPI, sem texto nativo) | `COMPLIANT` via OCR Tesseract (`tesseract-ocr-por`) |

Para regerar os três PDFs complementares (`cnd_federal_vencida.pdf`, `cnd_federal_sem_validade.pdf`
e `cnd_federal_digitalizada_ocr.pdf`), execute:

```bash
uv run python backend/scripts/generate_demo_samples.py
```

---

## 2. Preparação do Ambiente Antes da Apresentação

1. **Subir a stack e verificar saúde:**

```bash
make up
make smoke
```

2. **Criar dois usuários `ANALISTA` distintos para a revisão Quatro Olhos:**

```bash
python backend/scripts/create_api_user.py analista.maker ANALISTA
python backend/scripts/create_api_user.py analista.checker ANALISTA
```

Adicione as duas entradas JSON geradas na lista `API_USERS='[...]'` do `.env` (entre aspas
simples para evitar interpolação de `$` pelo Docker Compose), reinicie os serviços
(`docker compose --env-file .env -f infra/docker-compose.yml up -d backend worker`) e guarde as
duas chaves geradas em `analista.maker.key` e `analista.checker.key` fora do repositório.

3. **Configurar LLM opcional para regras híbridas (`#129`):**

No `.env` de demonstração (usando exclusivamente os PDFs fictícios de `docs/samples/`):

```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=particle-ai/particle-1:free
OPENAI_API_KEY=<chave-rotacionada-de-demo>
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=2
```

Caso `OPENAI_API_KEY` não esteja definida (ou ocorra `429`), as regras determinísticas continuam
operando normalmente e as regras híbridas seguem para revisão manual (`fail-closed`).

4. **Abrir o painel web e verificar a API:**

- Interface do Analista: [http://localhost:5173](http://localhost:5173) (indicador `API Online` no cabeçalho).
- Swagger / OpenAPI (apoio técnico): [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 3. Sequência da Demonstração (5 Atos)

### Ato 1: CND Federal Válida (`COMPLIANT`)

1. Na aba **Ingestão Documental (IDP)**, envie `docs/samples/cnd_federal_ficticia_apresentacao.pdf`.
2. Acompanhe o status evoluir automaticamente de `Na Fila` / `Processando OCR/IDP...` para `Concluído`.
3. Clique em **Verificar Conformidade**.
4. Mostre no laudo:
   - Status geral **Conforme** (`100%`, `1 / 1` regra aplicável);
   - Tipologia identificada `CND_FEDERAL` e demais regras marcadas como **Não Aplicável**;
   - Seção **Evidências e Campos Extraídos por Página** com `cnpj`, `data_validade` (`2027-05-15`), `situacao` e os trechos literais com `Pág. 1`.

### Ato 2: CND Federal Vencida (`NON_COMPLIANT`)

1. Envie `docs/samples/cnd_federal_vencida.pdf` (`Valida ate: 10/07/2025`).
2. Após concluir, clique em **Verificar Conformidade**.
3. Mostre no laudo:
   - Status geral **Não Conforme** (`0%`), bloqueado pela validade vencida da `RULE-BNDES-001`;
   - Campo `data_validade` extraído (`2025-07-10`) e trecho literal ancorado na página 1.

### Ato 3: CND Federal Sem Validade Legível (`MANUAL_REVIEW_REQUIRED`)

1. Envie `docs/samples/cnd_federal_sem_validade.pdf` (`Data de validade: [campo ilegivel / rasurado na emissao]`).
2. Clique em **Verificar Conformidade**.
3. Mostre no laudo:
   - Status geral **Revisão Manual** (princípio do projeto: ausência de data legível nunca aprova);
   - Apontamento `Data de validade da certidao nao identificada de forma legivel` na regra `RULE-BNDES-001`.

### Ato 4: Decisão Humana Segregada por Dois Analistas (`RF09`)

Usando o laudo do Ato 3 (ou o do Ato 2 para demonstrar exceção motivada / reprovação):

1. **Analista 1 (`analista.maker`):**
   - Clique em **Informar Chave** no cabeçalho e insira a chave de `analista.maker` (armazenada apenas em memória na sessão).
   - No painel **Revisão Humana (Maker-Checker / Quatro Olhos)**, selecione a decisão (`Reprovar Laudo` ou `Aprovar com Exceção Motivada` se for `NON_COMPLIANT`; `Aprovar Laudo` se o documento de revisão manual tiver sido conferido) e preencha uma justificativa técnica com ao menos 20 caracteres.
   - Envie a proposta (`Enviar Proposta (Maker)`). O estado muda para `Aguardando 2º Analista`.
2. **Prova de segregação de funções:**
   - Ainda autenticado como `analista.maker`, mostre o alerta **Segregação de funções** bloqueando os botões **Confirmar Proposta** e **Devolver Proposta** (no backend, qualquer chamada direta pelo mesmo ator retorna `HTTP 403`).
3. **Analista 2 (`analista.checker`):**
   - Clique em `Analista: analista.maker` no cabeçalho e troque para a chave de `analista.checker`.
   - Registre o parecer do revisor (mínimo 10 caracteres) e clique em **Confirmar Proposta**.
   - Mostre o estado evoluindo para `Revisão Concluída` (`FINAL`) com o histórico imutável de eventos (`PROPOSED` e `CONFIRMED`) exibindo os dois executores distintos.

### Ato 5: Trilha de Auditoria Imutável (`RF10`)

1. Abra a aba **Trilha de Auditoria** e clique em **Atualizar Logs**.
2. Mostre a sequência cronológica gravada no banco (`append-only`):
   - `DOCUMENT_UPLOADED` (contendo `sha256` do PDF enviado);
   - `COMPLIANCE_EVALUATION` (status, tipologia, score e `HARNESS_RULES_ENGINE`);
   - `REVIEW_PROPOSED` (autor `analista.maker`, decisão e justificativa);
   - `REVIEW_CONFIRMED` (autor `analista.checker` e parecer).

---

## 4. Plano B para Falha de OCR e Falha de LLM

### Plano B para falha de OCR

Se o envio de `docs/samples/cnd_federal_digitalizada_ocr.pdf` falhar na apresentação (por exemplo,
erro de `tesseract` no worker, falta do pacote `por` ou lentidão de CPU na máquina de demo):

1. **Diagnóstico rápido (opcional, fora da apresentação):**

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python scripts/validate_ocr_container.py
```

2. **Contingência imediata ao vivo:**
   - Utilize `docs/samples/cnd_federal_ficticia_apresentacao.pdf`, `docs/samples/cnd_federal_vencida.pdf`
     e `docs/samples/cnd_federal_sem_validade.pdf` (PDFs com camada de texto nativa extraída via
     `pdfplumber`, sem depender do binário `tesseract`).
   - Se precisar mostrar o comportamento do OCR já comprovado no pipeline, apresente a saída
     registrada do `validate_ocr_container.py` em [Relatório de Validação](VALIDATION_REPORT.md)
     e o job verde `Backend / Build` no GitHub Actions.

### Plano B para falha ou cota do provedor LLM (`429` / `LLM_UNAVAILABLE`)

Se o OpenRouter retornar `429` após as retentativas ou estiver sem chave no ambiente:

- Não interrompa a demonstração: explique que o comportamento **fail-closed** (`T03b`) encaminha a
  regra híbrida para `MANUAL_REVIEW_REQUIRED` (`error: LLM_UNAVAILABLE`) e siga diretamente para o
  Ato 4 (revisão humana por dois analistas).

---

## 5. Checklist de Ensaio (Pré-Demonstração)

- [ ] `make up && make smoke` executado com código `0` na máquina da apresentação.
- [ ] Chaves `analista.maker` e `analista.checker` testadas no navegador sem uso de acesso anônimo.
- [ ] Todos os 5 atos executados em sequência no ambiente de apresentação.
- [ ] Plano B de OCR testado (confirmar que os PDFs nativos de `docs/samples/` concluem sem `tesseract`).
- [ ] Se usar OpenRouter na demo: confirmar chave rotacionada e validar uma regra `HYBRID` antes da sessão.

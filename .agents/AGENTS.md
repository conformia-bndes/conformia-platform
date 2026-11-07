# Diretrizes de Harness Engineering e Operação de Agentes - Conform.IA BNDES

Este documento estabelece o contexto operacional, os limites de autonomia e as diretrizes agent-first para agentes autônomos de IA e desenvolvedores que atuam no repositório `conformia-platform` da organização `conformia-bndes`.

---

## Contexto e Missão do Projeto
O Conform.IA BNDES é uma plataforma SaaS de Processamento Inteligente de Documentos (IDP) e Auditoria Imutável concebida para atender aos requisitos da Consulta Pública BNDES nº 01/2025.

O sistema automatiza a conferência de conformidade cadastral, fiscal, trabalhista, jurídica e socioambiental de proponentes e operações de crédito/investimento no BNDES. Em operações que envolvem recursos públicos federais, a confiabilidade é absoluta: nenhuma certidão inválida ou com pendências pode ser aprovada por alucinação de modelo.

---

## Princípios de Harness Engineering

### 1. Contexto Rigorosamente Delimitado
- Os agentes operam sob contexto injetado controlado, recebendo apenas os trechos documentais relevantes, esquemas formais e regras explicitas.
- Nunca alimente prompts com instruções permissivas ou prompts sem delimitação clara de formato (sempre exigir esquemas JSON validados por Pydantic/JSON Schema).

### 2. Padrão Maker-Checker (Quatro Olhos Algorítmico)
- Maker (Propositor):
  - Analisa o texto extraído do documento e formula uma hipótese de conformidade (`COMPLIANT`, `NON_COMPLIANT`, `MANUAL_REVIEW_REQUIRED`).
  - E obrigado a apontar a citação literal exata da evidência no texto original.
- Checker (Crítico / Auditor):
  - Avalia a proposta do Maker de forma isolada.
  - Verifica se a evidência alegada realmente existe no documento e se não houve extrapolação semântica ou alucinação.
  - Se o Checker rejeitar a evidência ou detectar inconsistência, o status e obrigatoriamente degradado para `MANUAL_REVIEW_REQUIRED`.
- Intervenção Humana (Human-in-the-Loop): Casos de divergência entre Maker e Checker são encaminhados para a interface de revisão do analista BNDES.

### 3. Ferramentas Delimitadas e Mínimo Privilégio
- As ferramentas acessiveis aos agentes de extração são somente leitura sobre o documento.
- Ferramentas com efeitos colaterais (gravação no banco, disparo de filas, criação de arquivos) possuem trilha de auditoria em `audit_logs` registrando o agente executor e timestamp UTC.

---

## Limites Operacionais e Anti-Padrões

1. Nunca Assumir Validade por Ausência de Dados:
   - Se uma certidão não contém a data de validade de forma legível, ela deve ser marcada como `MANUAL_REVIEW_REQUIRED`, nunca como `COMPLIANT`.
2. Nunca Executar Comandos Destrutivos:
   - Agentes não devem executar `drop table`, `rm -rf`, resets de banco ou commits com `--force`.
3. Não Expor Dados Pessoais Sensíveis (LGPD / PII):
   - Logs e traces OpenTelemetry não devem conter CPF, dados bancários de socios ou credenciais.
4. Respeito aos Contratos de Schema:
   - Qualquer alteração em `rules/schemas/` exige validação prévia de compatibilidade com a suíte em `evals/eval_pipeline.py`.

---

## Organização das Responsabilidades de Código

| Diretório | Responsabilidade Primária | Equipe Mantenedora |
| :--- | :--- | :--- |
| `backend/app/idp/` | Pipeline de extração PDF/OCR | `@conformia-bndes/backend` |
| `backend/app/ai/` | Orquestração LLM e Maker-Checker | `@conformia-bndes/ai-evals` |
| `backend/app/services/` | Motor de regras determinísticas | `@conformia-bndes/backend` |
| `rules/schemas/` | Esquemas e checklists normativos | `@conformia-bndes/backend` `@conformia-bndes/maintainers` |
| `evals/` | Benchmarks de acurácia e regressão | `@conformia-bndes/ai-evals` |
| `frontend/` | Interface React/Tailwind para analistas | `@conformia-bndes/frontend` |
| `infra/` | Docker Compose e infraestrutura | `@conformia-bndes/devops` |
| `docs/` | Documentação técnica e ADRs | `@conformia-bndes/maintainers` `@conformia-bndes/qa` |
| `.agents/` | Contexto de Harness e diretrizes | `@conformia-bndes/ai-evals` `@conformia-bndes/maintainers` |

---

## Protocolo de Validação Antes de Commits
Antes de concluir qualquer tarefa automatizada, o agente deve validar:
```bash
# 1. Testes de backend e regras
pytest backend/tests/ -v

# 2. Benchmark de regressao de Evals
python evals/eval_pipeline.py

# 3. Linting e formatacao
black --check backend/
flake8 backend/
```

# Diretrizes de Harness Engineering e Operacao de Agentes - Conform.IA BNDES

Este documento estabelece o contexto operacional, os limites de autonomia e as diretrizes agent-first para agentes autonomos de IA e desenvolvedores que atuam no repositorio `conformia-platform` da organizacao `conformia-bndes`.

---

## Contexto e Missao do Projeto
O Conform.IA BNDES e uma plataforma SaaS de Processamento Inteligente de Documentos (IDP) e Auditoria Imutavel concebida para atender aos requisitos da Consulta Publica BNDES no 01/2025.

O sistema automatiza a conferencia de conformidade cadastral, fiscal, trabalhista, juridica e socioambiental de proponentes e operacoes de credito/investimento no BNDES. Em operacoes que envolvem recursos publicos federais, a confiabilidade e absoluta: nenhuma certidao invalida ou com pendencias pode ser aprovada por alucinacao de modelo.

---

## Principios de Harness Engineering

### 1. Contexto Rigorosamente Delimitado
- Os agentes operam sob contexto injetado controlado, recebendo apenas os trechos documentais relevantes, esquemas formais e regras explicitas.
- Nunca alimente prompts com instrucoes permissivas ou prompts sem delimitacao clara de formato (sempre exigir esquemas JSON validados por Pydantic/JSON Schema).

### 2. Padrao Maker-Checker (Quatro Olhos Algoritmico)
- Maker (Propositor):
  - Analisa o texto extraido do documento e formula uma hipotese de conformidade (`COMPLIANT`, `NON_COMPLIANT`, `MANUAL_REVIEW_REQUIRED`).
  - E obrigado a apontar a citacao literal exata da evidencia no texto original.
- Checker (Critico / Auditor):
  - Avalia a proposta do Maker de forma isolada.
  - Verifica se a evidencia alegada realmente existe no documento e se nao houve extrapolacao semantica ou alucinacao.
  - Se o Checker rejeitar a evidencia ou detectar inconsistencia, o status e obrigatoriamente degradado para `MANUAL_REVIEW_REQUIRED`.
- Intervencao Humana (Human-in-the-Loop): Casos de divergencia entre Maker e Checker sao encaminhados para a interface de revisao do analista BNDES.

### 3. Ferramentas Delimitadas e Minimo Privilegio
- As ferramentas acessiveis aos agentes de extracao sao somente leitura sobre o documento.
- Ferramentas com efeitos colaterais (gravacao no banco, disparo de filas, criacao de arquivos) possuem trilha de auditoria em `audit_logs` registrando o agente executor e timestamp UTC.

---

## Limites Operacionais e Anti-Padroes

1. Nunca Assumir Validade por Ausencia de Dados:
   - Se uma certidao nao contem a data de validade de forma legivel, ela deve ser marcada como `MANUAL_REVIEW_REQUIRED`, nunca como `COMPLIANT`.
2. Nunca Executar Comandos Destrutivos:
   - Agentes nao devem executar `drop table`, `rm -rf`, resets de banco ou commits com `--force`.
3. Nao Expor Dados Pessoais Sensiveis (LGPD / PII):
   - Logs e traces OpenTelemetry nao devem conter CPF, dados bancarios de socios ou credenciais.
4. Respeito aos Contratos de Schema:
   - Qualquer alteracao em `rules/schemas/` exige validacao previa de compatibilidade com a suite em `evals/eval_pipeline.py`.

---

## Organizacao das Responsabilidades de Codigo

| Diretorio | Responsabilidade Primaria | Equipe Mantenedora |
| :--- | :--- | :--- |
| `backend/app/idp/` | Pipeline de extracao PDF/OCR | `@conformia-bndes/backend` |
| `backend/app/ai/` | Orquestracao LLM e Maker-Checker | `@conformia-bndes/ai-evals` |
| `backend/app/services/` | Motor de regras deterministicas | `@conformia-bndes/backend` |
| `rules/schemas/` | Esquemas e checklists normativos | `@conformia-bndes/backend` `@conformia-bndes/maintainers` |
| `evals/` | Benchmarks de acuracia e regressao | `@conformia-bndes/ai-evals` |
| `frontend/` | Interface React/Tailwind para analistas | `@conformia-bndes/frontend` |
| `infra/` | Docker Compose e infraestrutura | `@conformia-bndes/devops` |
| `docs/` | Documentacao tecnica e ADRs | `@conformia-bndes/maintainers` `@conformia-bndes/qa` |
| `.agents/` | Contexto de Harness e diretrizes | `@conformia-bndes/ai-evals` `@conformia-bndes/maintainers` |

---

## Protocolo de Validacao Antes de Commits
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

# Protocolos de Qualidade e Quality Gates

O Conform.IA BNDES estabelece padroes rigorosos de qualidade, seguranca e conformidade que devem ser atendidos antes de qualquer commit ou integracao na branch `main`.

---

## 1. O Tripe de Qualidade

<div class="grid cards" markdown>

- ### 1. Verificacao Estatica
    Linter e formatacao automatica em Python (`black`, `flake8`) e TypeScript/React (`eslint`).

- ### 2. Testes de Regressao
    Suite completa de testes unitarios e de integracao via `pytest` (backend) e `vitest` (frontend).

- ### 3. Harness Evals
    Benchmark deterministico de acuracia documental com tolerancia zero a falsos positivos.

</div>

---

## 2. Comandos do Quality Gate Local

Antes de submeter um Pull Request, execute os comandos do gate de qualidade:

```bash
# 1. Execucao de Testes Automatizados
uv run pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing
cd frontend && npm test

# 2. Execucao do Benchmark de Evals
uv run python evals/eval_pipeline.py

# 3. Validacao de Linters e Formatacao
uv run black --check backend/
uv run flake8 backend/
cd frontend && npm run lint

# 4. Varredura Local de Segredos e Dependencias
gitleaks detect --source . --config .gitleaks.toml --verbose
pip-audit -r backend/requirements.txt
```

---

## 3. Politica Estrita de Ausencia de Emojis

Como a plataforma e destinada a atender requisitos institucionais de um banco publico de desenvolvimento federal (BNDES) e estara sujeita a auditorias de orgaos de controle externo (TCU, CGU):

- E **terminantemente proibido o uso de emojis** em:
  - Codigo-fonte (comentarios, variaveis, docstrings, retornos de API).
  - Documentacao tecnica (Markdown, MkDocs, README).
  - Templates de Pull Request e Issues.
  - Mensagens de commit do Git.
- A comunicacao deve ser estritamente tecnica, formal, sobria e precisa.

# Protocolos de Qualidade e Quality Gates

O Conform.IA BNDES estabelece padrões rigorosos de qualidade, segurança e conformidade que devem ser atendidos antes de qualquer commit ou integração na branch `main`.

---

## 1. O Tripé de Qualidade

<div class="grid cards" markdown>

- ### 1. Verificacao Estatica

  Linter e formatação automática em Python (`black`, `flake8`) e TypeScript/React (`eslint`).

- ### 2. Testes de Regressao

  Suíte completa de testes unitários e de integração via `pytest` (backend) e `vitest` (frontend).

- ### 3. Harness Evals
  Benchmark determinístico de acurácia documental com tolerância zero a falsos positivos.

</div>

---

## 2. Comandos do Quality Gate Local

Antes de submeter um Pull Request, execute os comandos do gate de qualidade:

```bash
# 1. Execução de Testes Automatizados
uv run pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing
cd frontend && npm test

# 2. Execução do Benchmark de Evals
uv run python evals/eval_pipeline.py

# 3. Validação de Linters e Formatação
uv run black --check backend/
uv run flake8 backend/
cd frontend && npm run lint

# 4. Varredura Local de Segredos e Dependências
gitleaks detect --source . --config .gitleaks.toml --verbose
pip-audit -r backend/requirements.txt
```

---

## 3. Política Estrita de Ausência de Emojis

Como a plataforma é destinada a atender requisitos institucionais de um banco público de desenvolvimento federal (BNDES) e estará sujeita a auditorias de órgãos de controle externo (TCU, CGU):

- É **terminantemente proibido o uso de emojis** em:
  - Codigo-fonte (comentarios, variaveis, docstrings, retornos de API).
  - Documentacao tecnica (Markdown, MkDocs, README).
  - Templates de Pull Request e Issues.
  - Mensagens de commit do Git.
- A comunicacao deve ser estritamente tecnica, formal, sobria e precisa.

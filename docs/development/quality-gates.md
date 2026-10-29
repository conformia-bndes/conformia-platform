# Protocolos de Qualidade e Quality Gates

O Conform.IA BNDES estabelece padrões rigorosos de qualidade, segurança e conformidade que devem ser atendidos antes de qualquer integração nas branches `dev` e `main`.

---

## 1. O Tripé de Qualidade

<div class="grid cards" markdown>

- ### 1. Verificação Estática

  Linter e formatação automática em Python (`black`, `flake8`) e TypeScript/React (`eslint`).

- ### 2. Testes de Regressão

  Suíte completa de testes unitários e de integração via `pytest` (backend) e `vitest` (frontend).

- ### 3. Harness Evals
  Benchmark determinístico de acurácia documental com tolerância zero a falsos positivos.

</div>

---

## 2. Comandos do Quality Gate Local

Os mesmos verificadores do CI, com as versões fixadas no `uv.lock`:

```bash
make hooks        # uma vez por clone: instala os hooks do pre-commit
make lint         # flake8, black e ESLint
make test         # pytest e Vitest
make eval         # benchmark de regras: 0 falsos positivos e acurácia mínima de 90%
make docs-build   # documentação em modo estrito
```

Verificações de segurança, equivalentes ao job "Segurança" do CI:

```bash
uvx pre-commit@4.7.0 run gitleaks --all-files
uv export --all-packages --all-extras --no-emit-workspace --no-hashes -o /tmp/req.txt
uvx pip-audit -r /tmp/req.txt --no-deps --disable-pip
cd frontend && npm audit --audit-level=high
```

No PR, o check obrigatório **CI OK** só fica verde quando todos os jobs afetados passam. Ver
[DevOps e CI/CD](devops.md).

---

## 3. Política Estrita de Ausência de Emojis

Como a plataforma é destinada a atender requisitos institucionais de um banco público de desenvolvimento federal (BNDES) e estará sujeita a auditorias de órgãos de controle externo (TCU, CGU):

- É **terminantemente proibido o uso de emojis** em:
  - Código-fonte (comentários, variáveis, docstrings, retornos de API).
  - Documentação técnica (Markdown, MkDocs, README).
  - Templates de Pull Request e Issues.
  - Mensagens de commit do Git.
- A comunicação deve ser estritamente técnica, formal, sóbria e precisa.

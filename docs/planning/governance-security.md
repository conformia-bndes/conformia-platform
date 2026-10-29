# Segurança, LGPD e Auditoria

Controles de segurança e privacidade implementados no MVP, riscos tratados e o que ainda falta
para um ambiente institucional. A automação de segurança do repositório (CodeQL, gitleaks,
Dependabot, rulesets) está em [Governança do repositório](../development/governance.md).

---

## 1. Controles implementados

| Controle | Como funciona |
| :-- | :-- |
| **Autenticação por chave pessoal** | Cada usuário tem uma chave `user_id:segredo`. O servidor guarda só o hash PBKDF2-HMAC-SHA256 com sal (mínimo de 100 mil iterações) em `API_USERS`. A chave é gerada por `backend/scripts/create_api_user.py` e gravada em arquivo privado, nunca exibida no terminal |
| **Autorização por perfil** | Perfis `ANALISTA`, `AUDITOR` e `ADMIN`. A revisão humana exige `ANALISTA` |
| **Segregação de funções** | Quem propõe uma decisão de revisão não pode confirmá-la |
| **Validação na entrada** | Upload só de PDF: extensão, assinatura binária `%PDF-` e tamanho máximo (HTTP 413 acima do limite) |
| **Integridade do documento** | SHA-256 do arquivo calculado na ingestão e exposto nos metadados |
| **Fail-closed** | LLM indisponível, resposta inválida, citação ausente ou validade ilegível resultam em `MANUAL_REVIEW_REQUIRED`, nunca em aprovação |
| **Segredos fora do código** | `.env` gerado por `make env` com valores aleatórios e fora do Git; gitleaks no pre-commit e no CI; secret scanning com push protection no GitHub |
| **CORS restrito** | Origens permitidas definidas em `ALLOWED_ORIGINS` |
| **Dados sintéticos** | Desenvolvimento, CI e benchmarks usam apenas documentos fictícios |

!!! danger "Ambientes de desenvolvimento e teste"
    Com `ENVIRONMENT` igual a `development` ou `test`, a API aceita requisições sem chave (exceto
    a revisão humana). Na demonstração, use `ENVIRONMENT=production` e cadastre os usuários em
    `API_USERS`.

---

## 2. Trilha de auditoria

| Registro | Onde | Conteúdo |
| :-- | :-- | :-- |
| Avaliação automática | `audit_logs` | Ação, documento, executor (`SYSTEM_HARNESS` ou usuário), detalhes da avaliação, data e hora |
| Laudo vigente | `compliance_checks` | Status por regra, confiança, evidência (trechos, termos e datas encontrados) e tipo de verificador |
| Decisão humana | `review_events` | Proposta e confirmação, decisão, justificativa, usuário e perfil; somente inserção |

O laudo e o registro de auditoria são gravados na mesma transação: ou os dois existem, ou
nenhum. Um reprocessamento substitui o laudo vigente, mas o histórico permanece em `audit_logs`.

---

## 3. Riscos e mitigação

| Risco | Severidade | Mitigação no MVP |
| :-- | :-- | :-- |
| Aprovação indevida por erro do LLM | Crítica | Maker-Checker com verificação literal da citação; o LLM só atua em regras híbridas, após a triagem determinística |
| OCR ruim em certidão digitalizada | Alta | Validade ilegível vai para revisão manual; benchmark sintético com documentos digitalizados |
| Vazamento de dados pessoais | Crítica | Somente dados sintéticos fora da produção; segredos fora do Git; chaves com hash |
| Mudança de regra sem controle | Alta | Checklist em JSON versionado, revisão por PR e benchmark obrigatório no CI |
| Dependência vulnerável | Alta | pip-audit e npm audit no CI, Dependabot e versões fixadas no `uv.lock` |

---

## 4. Pendente para produção

Fora do escopo do MVP e necessário antes de uso com dados reais:

- TLS na borda (proxy reverso) e criptografia em repouso no PostgreSQL e no MinIO.
- Política de retenção e descarte de documentos (LGPD, art. 15 e 16).
- Mascaramento de CPF e dados bancários em logs.
- Fluxo formal de exceção autorizada (decisão judicial ou da diretoria), com status próprio no
  laudo.
- Integração com identidade corporativa (SSO) no lugar das chaves pessoais.

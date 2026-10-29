# Governança do Repositório e Ferramentas

Como o time se organiza no GitHub e quais ferramentas garantem qualidade, segurança e
rastreabilidade. Atualizado em 29/10/2026.

---

## 1. Organização e responsabilidades

**Tech lead:** Pedro Henrique (`pedrohpsantos`): maintainer de todos os times e administrador
da organização.

| Time | Membros | Acesso ao repositório | Responsabilidade (CODEOWNERS) |
| :-- | :-- | :-- | :-- |
| `maintainers` | pedrohpsantos | Admin | Governança, `.github/`, `rules/`, `docs/` |
| `devops` | pedrohpsantos, arthurmgl99 | Maintain | `infra/`, CI/CD |
| `backend` | pedrohpsantos, LuizaCarvalho691 | Write | API, banco, IDP, regras |
| `frontend` | Mateiki, lucaspaulaleal, pedrohpsantos | Write | `frontend/` |
| `ai-evals` | Mateiki, alanafeitosa-ui, pedrohpsantos | Write | `backend/app/ai/`, `evals/`, `.agents/` |
| `qa` | Mateiki, pedrohpsantos | Write | `backend/tests/`, documentação |

!!! note "Por que os times precisam de acesso ao repositório"
    O GitHub só solicita revisão automática de um time listado no `CODEOWNERS` se o time tiver
    permissão de escrita. Até 29/10 os times não tinham acesso, e o roteamento de revisão não
    funcionava.

---

## 2. Planejamento visível

| Recurso | Uso |
| :-- | :-- |
| [Project do MVP](https://github.com/orgs/conformia-bndes/projects/2) | Visões **Kanban** (por status), **Roadmap** (por Início e Entrega) e **Backlog** (tabela) |
| Milestones M1-M6 | Marcos do plano de entrega, de 04/11 a 05/12/2026 |
| Labels `P0`/`P1`/`P2` | Prioridade (P0 bloqueia a entrega) |
| Labels `area: *` | Área técnica responsável |
| Label `decision` | Decisão humana pendente |

Status do Kanban: **Backlog → A fazer → Em andamento → Em revisão → Concluído**.

!!! tip "Roadmap"
    Se a visão Roadmap abrir sem datas, selecione **Início** e **Entrega** em
    *Date fields* (menu da visão). A API do GitHub ainda não permite configurar isso.

---

## 3. Ferramentas adotadas

| Ferramenta | Problema que resolve | Onde |
| :-- | :-- | :-- |
| **pre-commit** | Erros de formatação, segredos e YAML/JSON inválidos chegavam ao CI | `.pre-commit-config.yaml`, `make hooks` |
| **Conventional Commits no título do PR** | Histórico sem padrão impedia CHANGELOG automático | `pr-title.yml` (`amannn/action-semantic-pull-request`) |
| **actionlint** | Erros em workflows só apareciam ao executar | Job "Lint dos workflows" do `ci.yml` |
| **CodeQL** | Não havia análise estática de segurança (SAST) | `codeql.yml` |
| **OpenSSF Scorecard** | Sem medição das práticas de segurança da cadeia de suprimentos | `scorecard.yml` |
| **Dependabot agrupado em `dev`** | PRs de dependência isolados e direto em `main` | `.github/dependabot.yml` |
| **release-please** | Versões e CHANGELOG manuais | `release-please.yml`, `release-please-config.json` |
| **MLflow (local)** | Resultados de evals não eram comparáveis entre execuções | `evals/eval_pipeline.py --mlflow` |
| **promptfoo** | Comportamento do LLM sem teste reproduzível | `evals/promptfoo/`, `llm-evals.yml` |
| **GitHub Projects v2** | Planejamento só em Markdown | Project do MVP |

---

## 4. Avaliadas e não adotadas agora

| Ferramenta | Motivo |
| :-- | :-- |
| Renovate | Dependabot já atende; trocar agora não traz ganho antes de 05/12 |
| SonarCloud / Codecov | Serviços externos com cadastro e token; CodeQL e a cobertura do pytest cobrem o MVP |
| DVC | Datasets atuais são pequenos e gerados de forma determinística; reavaliar com PDFs reais |
| Langfuse / observabilidade de LLM | Exige servidor; o LLM ainda não é usado em produção |
| Trivy (scan de imagem) | Planejado junto da imagem reprodutível (issue de Docker no milestone M2) |
| Assinatura e proveniência (SLSA, cosign) | Sem publicação de imagens em registry no MVP |

---

## 5. Configuração do repositório

| Configuração | Estado |
| :-- | :-- |
| Ruleset `main-protection` | PR com 1 aprovação, descartada a cada novo push e que não pode vir de quem fez o último push; branch atualizada com `main`; check **CI OK** obrigatório; sem push forçado nem exclusão |
| Ruleset `dev-protection` | PR obrigatório, check **CI OK** obrigatório, sem push forçado nem exclusão; o bypass dos `maintainers` vale só para merge de PR |
| *Allow GitHub Actions to create and approve pull requests* | Habilitado na organização e no repositório (necessário ao release-please) |
| Code scanning (CodeQL) | Habilitado via `codeql.yml` |
| Secret scanning e push protection | Habilitados |

Somente o time `maintainers` pode ignorar os rulesets, e apenas para correções emergenciais. Em `dev`, esse bypass vale só para merge de PR: ninguém consegue apagar a branch nem fazer push direto, o que evita apagá-la pelo botão "Delete branch" após a promoção para `main`.

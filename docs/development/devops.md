# DevOps: Fluxo de Entrega e Operação

Como o código sai da máquina do desenvolvedor e chega à demonstração, com quais verificações
em cada etapa e como voltar atrás quando algo falha.

!!! info "Resumo"
    `feature/*` → PR para **`dev`** (integração) → PR de promoção para **`main`** →
    release-please abre o PR de versão → merge gera a tag `vX.Y.Z` e o GitHub Release.

---

## 1. Fluxo de branches

| Branch | Papel | Proteção |
| :-- | :-- | :-- |
| `main` | Versão estável e demonstrável; origem das releases | Ruleset `main-protection`: PR com 1 aprovação (descartada a cada novo push; quem fez o último push não aprova), branch atualizada e check **CI OK** verde, sem push forçado nem exclusão. Bypass do time `maintainers` |
| `dev` | Integração contínua do time | Ruleset `dev-protection`: PR obrigatório e check **CI OK** verde, sem push forçado nem exclusão. O time `maintainers` só ignora as regras ao mergear PRs: ninguém apaga `dev` nem faz push direto |
| `feat/*`, `fix/*`, `chore/*`, `docs/*` | Trabalho de uma issue | Abertas a partir de `dev` |

**Regras práticas**

1. Toda mudança começa em uma issue do [Project do MVP](https://github.com/orgs/conformia-bndes/projects/2).
2. O título do PR segue **Conventional Commits** (`feat:`, `fix:`, `docs:`, `sec:`...). O workflow
   `pr-title.yml` valida o título; o release-please usa os tipos para gerar o CHANGELOG.
3. PRs empilhados são permitidos: a base é o PR anterior e muda para `dev` após o merge dele.
4. Dependabot abre PRs em `dev`, com atualizações minor e patch agrupadas.

---

## 2. Pipelines (GitHub Actions)

O `ci.yml` é só o orquestrador. Cada área é um **workflow reutilizável** (`ci-repo.yml`,
`ci-backend.yml`, `ci-frontend.yml`, `ci-infra.yml`). O critério de organização é simples: o que
é barato fica junto num job (um só `uv sync` ou `npm ci`), e só o que é pesado ganha job próprio.
São cerca de 10 jobs em vez de 21. O job **CI OK** consolida as áreas e é o único check
obrigatório nos rulesets: área pulada (sem mudança) aprova; falha ou cancelamento bloqueia.

```mermaid
flowchart LR
    changes["Changes"] --> backend & frontend & infra & docs
    subgraph Repo
        rc["Checks<br/>higiene + gitleaks"]
    end
    subgraph Backend
        direction TB
        bq["Quality<br/>black, flake8, evals, pip-audit"]
        bt["Tests (3.11 e 3.12)<br/>matriz"]
        bf["Fuzz<br/>Atheris 60 s"]
    end
    subgraph Frontend
        fq["Quality<br/>ESLint, Vitest, build, audit"]
    end
    subgraph Infra
        direction TB
        il["Lint<br/>actionlint + compose"]
        im["Smoke<br/>Docker Compose"]
    end
    Repo --> ok["CI OK"]
    Backend --> ok
    Frontend --> ok
    Infra --> ok
    docs["Docs<br/>build estrito"] --> ok
```

Nenhuma área espera a outra, então o tempo total é o do job mais lento (smoke em Docker, fuzzing
ou testes, cerca de 2 minutos). O filtro por caminho (job `changes`) pula as áreas que o PR não
toca; em push para `main`/`dev`, execução manual e na execução semanal (segunda, 06:00 UTC) tudo
roda.

| Área | Jobs | O que garante |
| :-- | :-- | :-- |
| Repo | Checks | Hooks de higiene do pre-commit (YAML, JSON, chaves privadas, espaços) e gitleaks no histórico completo |
| Backend | Quality, Tests (matriz), Fuzz | black e flake8; benchmark de regras (0 falsos positivos); pip-audit; pytest com cobertura em Python 3.11 (produto) e 3.12 (compatibilidade); fuzzing Atheris de 60 s |
| Frontend | Quality | ESLint; Vitest; typecheck e build de produção; `npm audit` |
| Infra | Lint, Smoke | actionlint e validação do `docker-compose.yml`; stack completa em Docker Compose com imagens em cache (upload → fila → worker) |
| Docs | Docs | `mkdocs build --strict` com a verificação do site |

### Relatórios de qualidade

Cada área publica artefatos `relatorio-*` (retenção de 30 dias): resultados de testes (JUnit),
cobertura (XML), benchmark de regras, estatísticas do fuzzing e auditorias de dependências. A
cobertura também aparece no resumo de cada execução do CI.

O `docs.yml` roda depois que o CI de `main` termina com sucesso, baixa esses artefatos e o
hook `docs_hooks/relatorios.py` monta a página [Relatórios de Qualidade](../relatorios/index.md)
do site. Localmente, `make reports` gera os mesmos arquivos em `reports/` e `make docs` os exibe.
A publicação só acontece a partir de push em `main`, nunca de PR.

Outros workflows:

| Workflow | Gatilho | O que garante |
| :-- | :-- | :-- |
| `pr-title.yml` | abertura e edição de PR | Título do PR em Conventional Commits |
| `codeql.yml` | push, PR e semanal | Análise estática de segurança (Python, TypeScript e os próprios workflows) |
| `scorecard.yml` | push em `main` e semanal | OpenSSF Scorecard: práticas de segurança da cadeia de suprimentos |
| `release-please.yml` | push em `main` | PR de release com versão semântica e CHANGELOG |
| `docs.yml` | CI de `main` concluído | Publicação desta documentação, com os relatórios de qualidade, no GitHub Pages (artefato, sem branch `gh-pages`) |
| `llm-evals.yml` | manual | Testes do Maker-Checker com LLM real (promptfoo); consome créditos |

**Cadeia de suprimentos.** Todas as actions são fixadas por SHA de commit (com a versão em
comentário), as imagens Docker por digest e o binário do gitleaks por checksum. Cada workflow
declara permissões mínimas (`contents: read` por padrão). O Dependabot atualiza SHAs, digests e
o `uv.lock` em PRs agrupados para `dev`.

**Acrescentar um check.** Crie o job no workflow da área (`ci-<área>.yml`); o gate da área e o
**CI OK** já o consideram. Nenhuma regra de branch precisa ser alterada.

!!! warning "Permissão necessária para o release-please"
    O release-please abre PRs com o `GITHUB_TOKEN`. Em **Settings → Actions → General**, a opção
    *Allow GitHub Actions to create and approve pull requests* precisa estar habilitada (na
    organização e no repositório).

---

## 3. Verificações locais antes do push

```bash
make hooks        # uma vez por clone: instala os hooks pre-commit
make lint         # flake8, black e ESLint
make test         # pytest e Vitest
make eval         # benchmark de regras (0 falsos positivos obrigatório)
make docs-build   # documentação em modo estrito
```

Os hooks rodam black e flake8 com as versões do `uv.lock` (as mesmas do CI), além de gitleaks,
detecção de chaves privadas e validação de YAML/JSON.

---

## 4. Ambientes e configuração

| Ambiente | Como sobe | Observações |
| :-- | :-- | :-- |
| Local | `make up` + `make smoke` | `.env` gerado por `make env` com segredos aleatórios; nada versionado |
| CI | Serviços efêmeros do GitHub Actions | `.env` gerado a cada execução |
| Demonstração | `make up` na máquina de demo, a partir da tag da release | `ENVIRONMENT` diferente de `development`; usuários em `API_USERS` |

!!! danger "Antes da demonstração"
    Em `development` e `test` a API aceita requisições sem chave (exceto a revisão humana).
    No ambiente de demonstração, defina `ENVIRONMENT=production` e cadastre os analistas em
    `API_USERS` (`python backend/scripts/create_api_user.py <user_id> ANALISTA`).

---

## 5. Release e rollback

**Release**

1. Promover `dev` para `main` por PR.
2. O release-please atualiza o PR de release (versão em `pyproject.toml`,
   `backend/pyproject.toml`, `frontend/package.json` e `config.py`, mais o CHANGELOG).
3. Merge do PR de release → tag `vX.Y.Z` e GitHub Release.

**Rollback**

| Situação | Ação |
| :-- | :-- |
| Defeito na aplicação | `git checkout <tag-anterior>` e `make up` no ambiente afetado |
| Migration problemática | `alembic downgrade -1` **somente** em banco descartável ou após backup; no ambiente de demo, restaurar o volume do PostgreSQL |
| Dependência quebrada | Reverter o PR do Dependabot (`git revert -m 1 <merge>`) |

---

## 6. Diagnóstico rápido

| Sintoma | Onde olhar |
| :-- | :-- |
| `make up` não fica saudável | `make ps`; `GET /api/v1/health` mostra qual dependência está `degraded` |
| Upload retorna 503 | Redis ou MinIO indisponível |
| Documento preso em `PROCESSING` | Logs do `worker` (`make logs`); estado em `GET /api/v1/documents/tasks/{task_id}` |
| Revisão humana retorna 401 | Usuário ausente em `API_USERS` ou chave errada |
| CI do PR não rodou | Base do PR precisa ser `main` ou `dev` |

# ADR-002: Adocao do Astral uv como Gerenciador de Pacotes e Workspace

| Parametro | Detalhe |
| :--- | :--- |
| **Status** | Aprovado |
| **Data** | 2026-09-27 |
| **Autor** | Equipe de Engenharia Conform.IA BNDES |
| **Decisores** | Staff Software Engineers |

---

## 1. Contexto e Problema

O ecossistema Python tradicionalmente dependia de multiplas ferramentas fragmentadas para gestao de dependencias e ambientes virtuais (`pip`, `virtualenv`, `pip-tools`, `poetry`). No contexto deste monorepo, a instalacao de dependencias pesadas no Docker e nos ambientes locais de desenvolvedores enfrentava tempos de build elevados (dezenas de segundos por container) e risco de inconsistencias entre desenvolvedores pela ausencia de um lockfile unificado de workspace.

## 2. Decisao

Adotou-se o **Astral `uv`** como ferramenta oficial e unificada para o gerenciamento de pacotes, resolucao de dependencias e workspaces Python no projeto Conform.IA BNDES.

As diretrizes tecnicas implementadas abrangem:
1. Configuracao de workspace nativo no root `pyproject.toml` (`[tool.uv.workspace] members = ["backend"]`).
2. Geracao e manutencao compulsoria do lockfile deterministico `uv.lock`.
3. Integracao multi-stage no Dockerfile via imagem oficial `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/`.
4. Utilizacao da action oficial `astral-sh/setup-uv@v5` com cache no GitHub Actions CI.
5. Suporte transparente no `Makefile` com deteccao automatica do utilitario `uv`.

## 3. Consequencias e Compensacoes

### Positivas:
- **Velocidade Extrema**: Resolucao e instalacao de dependencias reduzida de ~45s para < 1s localmente e 160ms em containers Docker.
- **Determinismo Absoluto**: O `uv.lock` garante que exatamente os mesmos hashes SHA-256 de pacotes sejam instalados em desenvolvimento, CI e producao.
- **Simplificacao Operacional**: Eliminou a necessidade de gerenciar multiplas ferramentas ou scripts complexos de ativacao de virtualenv.

### Negativas / Mitigacoes:
- Exige que novos colaboradores tenham o binario do `uv` instalado em suas maquinas de desenvolvimento (documentado no `README.md` e mitigado pelo fallback automatico para `pip` no `Makefile`).

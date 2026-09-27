# ADR-002: Adoção do Astral uv como Gerenciador de Pacotes e Workspace

## Metadados

- **Status**: Aprovado
- **Data**: 2026-09-27
- **Autores**: Equipe de Engenharia Conform.IA BNDES
- **Revisores**: Staff Software Engineers
- **Épico / Requisito**: Consulta Pública BNDES nº 01/2025

---

## 1. Contexto e Declaração do Problema

O ecossistema Python tradicionalmente dependia de múltiplas ferramentas fragmentadas para gestão de dependências e ambientes virtuais (`pip`, `virtualenv`, `pip-tools`, `poetry`). Neste monorepo, a instalação de dependências pesadas no Docker e nos ambientes locais enfrentava tempos de build elevados (dezenas de segundos por contêiner) e risco de inconsistências entre desenvolvedores pela ausência de um lockfile unificado de workspace.

## 2. Opções Consideradas

### Opção 1: Ferramentas Python Fragmentadas

- Manter a combinação de `pip`, `virtualenv`, `pip-tools` ou `poetry` conforme a necessidade de cada ambiente.
- _Vantagens_: familiaridade da equipe e ampla disponibilidade no ecossistema Python.
- _Desvantagens_: resolução mais lenta, múltiplos arquivos de configuração e ausência de uma experiência unificada de workspace.

### Opção 2: Astral uv (Opção Escolhida)

- Adotar o `uv` como ferramenta única para resolução, instalação, execução e gerenciamento do workspace.
- _Vantagens_: velocidade, lockfile determinístico e integração nativa com workspaces.
- _Desvantagens_: exige que novos colaboradores conheçam e instalem o binário do `uv`.

## 3. Decisão Adotada

Adota-se o **Astral `uv`** como ferramenta oficial e unificada para o gerenciamento de pacotes, resolução de dependências e workspaces Python no projeto Conform.IA BNDES.

As diretrizes técnicas implementadas abrangem:

1. Configuração de workspace nativo no `pyproject.toml` raiz (`[tool.uv.workspace] members = ["backend"]`).
2. Geração e manutenção obrigatórias do lockfile determinístico `uv.lock`.
3. Integração multi-stage no Dockerfile por meio da imagem oficial `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/`.
4. Utilização da action oficial `astral-sh/setup-uv@v5`, com cache no GitHub Actions CI.
5. Suporte transparente no `Makefile`, com detecção automática do utilitário `uv`.

## 4. Consequências e Compensações (Trade-offs)

### Impactos Positivos

- **Velocidade**: Resolução e instalação de dependências reduzidas de aproximadamente 45 s para menos de 1 s localmente e 160 ms em contêineres Docker.
- **Determinismo**: O `uv.lock` garante que os mesmos hashes SHA-256 de pacotes sejam instalados em desenvolvimento, CI e produção.
- **Simplificação Operacional**: Reduz a necessidade de gerenciar múltiplas ferramentas ou scripts complexos de ativação de ambientes virtuais.

### Impactos Negativos e Riscos

- Exige que novos colaboradores tenham o binário do `uv` instalado em suas máquinas de desenvolvimento.
- Mitigação: o requisito é documentado no `README.md`, e o `Makefile` mantém fallback automático para `pip`.

## 5. Diretrizes de Implementação e Auditoria

1. Alterações nas dependências devem atualizar o `pyproject.toml` e o `uv.lock` no mesmo PR.
2. O CI deve usar a versão do `uv` definida pelo workflow e validar a instalação a partir do lockfile.
3. A documentação de desenvolvimento deve manter instruções equivalentes para `uv` e para o fallback com `pip` quando aplicável.

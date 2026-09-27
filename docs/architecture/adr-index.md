# Indice de Registros de Decisao Arquitetural (ADRs)

Este documento centraliza todos os Registros de Decisao Arquitetural (Architectural Decision Records - ADRs) do projeto Conform.IA BNDES. As decisoes aqui registradas documentam escolhas estruturais, compensacoes tecnicas (trade-offs) e diretrizes adotadas.

---

## Processo de Submissao de ADRs

Para propor uma nova decisao arquitetural:
1. Copie o arquivo modelo [`adr-template.md`](adr-template.md).
2. Nomeie o novo arquivo seguindo o padrao incremental: `adr-XXX-nome-da-decisao.md`.
3. Preencha todos os campos tecnicos obrigatorios (Status, Contexto, Decisao, Consequencias).
4. Submeta via Pull Request para revisao das equipes mantenedoras (@conformia-bndes/maintainers).

---

## Tabela de Decisoes Arquiteturais

| Identificador | Titulo | Status | Data | Autores |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-001](adr-001-monorepo-modular.md) | Adocao de Monorepo Modular e Harness Engineering | Aprovado | 2026-09-26 | Conform.IA Engineering Team |
| [ADR-002](adr-002-astral-uv-toolchain.md) | Adocao do Astral uv como Gerenciador de Pacotes e Workspace | Aprovado | 2026-09-27 | Conform.IA Engineering Team |
| [ADR-003](adr-003-spa-vs-nextjs.md) | Adocao de React + Vite SPA em Substituicao ao Next.js para o Cockpit Operacional | Aprovado | 2026-09-27 | Conform.IA Engineering Team |

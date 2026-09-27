# Índice de Registros de Decisão Arquitetural (ADRs)

Este documento centraliza todos os Registros de Decisão Arquitetural (Architectural Decision Records — ADRs) do projeto Conform.IA BNDES. As decisões aqui registradas documentam escolhas estruturais, compensações técnicas (trade-offs) e diretrizes adotadas.

---

## Processo de Submissao de ADRs

Para propor uma nova decisão arquitetural:

1. Copie o arquivo modelo [`adr-template.md`](adr-template.md).
2. Nomeie o novo arquivo seguindo o padrão incremental: `adr-XXX-nome-da-decisao.md`.
3. Preencha todos os campos técnicos obrigatórios (Status, Contexto, Decisão, Consequências).
4. Submeta via Pull Request para revisão das equipes mantenedoras (@conformia-bndes/maintainers).

---

## Tabela de Decisoes Arquiteturais

| Identificador                             | Titulo                                                                           | Status   | Data       | Autores                     |
| :---------------------------------------- | :------------------------------------------------------------------------------- | :------- | :--------- | :-------------------------- |
| [ADR-001](adr-001-monorepo-modular.md)    | Adoção de Monorepo Modular e Harness Engineering                                 | Aprovado | 2026-09-26 | Conform.IA Engineering Team |
| [ADR-002](adr-002-astral-uv-toolchain.md) | Adoção do Astral uv como Gerenciador de Pacotes e Workspace                      | Aprovado | 2026-09-27 | Conform.IA Engineering Team |
| [ADR-003](adr-003-spa-vs-nextjs.md)       | Adoção de React + Vite SPA em Substituição ao Next.js para o Cockpit Operacional | Aprovado | 2026-09-27 | Conform.IA Engineering Team |

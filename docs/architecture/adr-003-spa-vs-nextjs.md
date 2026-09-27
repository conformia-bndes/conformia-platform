# ADR-003: Adocao de React + Vite SPA em Substituicao ao Next.js para o Cockpit Operacional

| Parametro | Detalhe |
| :--- | :--- |
| **Status** | Aprovado |
| **Data** | 2026-09-27 |
| **Autor** | Equipe de Engenharia Conform.IA BNDES |
| **Decisores** | Staff Software Engineers & Arquitetura de Solucoes |

---

## 1. Contexto e Problema

Durante a definicao da camada de apresentacao da plataforma Conform.IA BNDES, cogitou-se a utilizacao do framework **Next.js** (React Server Components / SSR) para o desenvolvimento do frontend.

A equipe realizou uma avaliacao arquitetural comparando **Next.js** com a abordagem de **Single Page Application (SPA) baseada em React 18 + Vite + Tailwind CSS**, considerando as caracteristicas operacionais do desafio do BNDES:
1. Trata-se de uma aplicacao corporativa interna (intranet/cockpit de analistas de credito), protegida integralmente por autenticacao e controle de acesso (RBAC).
2. O sistema exige a renderizacao interativa de documentos PDF em tela dividida (*split-view*) com marcacoes dinamicas de coordenadas (*bounding boxes*).
3. Todo o processamento de regras, IA, OCR e banco de dados reside no backend Python/FastAPI.

## 2. Decisao

Decidiu-se **manter e consolidar o frontend como uma Single Page Application (SPA) estatica utilizando React 18, Vite, TypeScript e Tailwind CSS**, rejeitando a adocao do Next.js para este caso de uso.

### Justificativas Tecnicas da Decisao:

1. **Inexistencia de Requisito de SEO**:
   O Next.js tem seu valor comprovado em portais publicos, e-commerces e aplicacoes que dependem de indexacao por robos de busca (SEO). O Conform.IA BNDES e um cockpit fechado e autenticado; o Server-Side Rendering (SSR) nao agrega nenhum valor de negocio ao produto.
2. **Eliminacao de Servidor Intermediario Desnecessario (BFF Fantasma)**:
   A adocao do Next.js obrigaria a manutencao de um servidor Node.js em producao apenas para intermediar HTML e chamadas de API para o FastAPI. Com React + Vite, o build produz artefatos estaticos puros servidos por um proxy reverso **Nginx** (container leve de menos de 25MB, consumo minimo de CPU/RAM e cache HTTP de borda).
3. **Evitacao de Conflitos de Hidratacao com Visualizadores de PDF e Canvas**:
   Bibliotecas de inspecao de PDFs no browser (`pdfjs-dist`, `react-pdf`) dependem exclusivamente de objetos do navegador (`window`, `document`, `HTMLCanvasElement`). No ambiente SSR do Next.js, essas ferramentas geram recorrentes erros de hidratacao e obrigam o uso de diretivas `'use client'` e imports dinamicos sem SSR em quase todas as telas operacionais.
4. **Desempenho e Produtividade**:
   O Vite oferece Hot Module Replacement (HMR) em milissegundos e pipeline de testes nativo com Vitest, maximizando a velocidade de iteracao da equipe.

## 3. Consequencias e Compensacoes

### Positivas:
- Infraestrutura mais simples e economica (menos um container de runtime pesado na stack Docker).
- Zero atrito no desenvolvimento de recursos visuais complexos de PDF e marcacoes de evidencia.
- Pipeline de CI/CD para o frontend extremamente rapido (build estatico em menos de 20 segundos).

### Negativas / Mitigacoes:
- O carregamento inicial depende do download do bundle JavaScript (mitigado por code-splitting via `React.lazy`, Vite e compressao gzip/brotli no Nginx).
- Gerenciamento de estado assincrono e cache de dados de rede devem ser conduzidos no cliente (mitigado pela adocao do `@tanstack/react-query`).

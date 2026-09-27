# ADR-003: Adoção de React + Vite SPA em Substituição ao Next.js para o Cockpit Operacional

## Metadados

| Parâmetro             | Detalhe                                            |
| :-------------------- | :------------------------------------------------- |
| **Status**            | Aprovado                                           |
| **Data**              | 2026-09-27                                         |
| **Autores**           | Equipe de Engenharia Conform.IA BNDES              |
| **Revisores**         | Staff Software Engineers e Arquitetura de Soluções |
| **Épico / Requisito** | Consulta Pública BNDES nº 01/2025                  |

---

## 1. Contexto e Declaração do Problema

Durante a definição da camada de apresentação da plataforma Conform.IA BNDES, considerou-se a utilização do framework **Next.js** (React Server Components / SSR) para o desenvolvimento do frontend.

A equipe realizou uma avaliação arquitetural comparando **Next.js** com a abordagem de **Single Page Application (SPA) baseada em React 18 + Vite + Tailwind CSS**, considerando as características operacionais do desafio do BNDES:

1. Trata-se de uma aplicação corporativa interna (intranet/cockpit de analistas de crédito), protegida integralmente por autenticação e controle de acesso (RBAC).
2. O sistema exige a renderização interativa de documentos PDF em tela dividida (_split-view_), com marcações dinâmicas de coordenadas (_bounding boxes_).
3. Todo o processamento de regras, IA, OCR e banco de dados reside no backend Python/FastAPI.

## 2. Opções Consideradas

### Opção 1: Next.js com SSR

- Utilizar Next.js, React Server Components e renderização no servidor para o cockpit.
- _Vantagens_: ecossistema integrado, SSR e recursos avançados de roteamento.
- _Desvantagens_: adiciona um servidor Node.js intermediário e aumenta a complexidade de integração com visualizadores PDF dependentes do navegador.

### Opção 2: React + Vite SPA (Opção Escolhida)

- Utilizar React 18, Vite, TypeScript e Tailwind CSS em uma SPA estática.
- _Vantagens_: distribuição simples por Nginx, desenvolvimento rápido e compatibilidade direta com APIs do navegador.
- _Desvantagens_: o carregamento inicial depende do bundle JavaScript e o estado de rede precisa ser gerenciado no cliente.

## 3. Decisão Adotada

Decide-se **manter e consolidar o frontend como uma Single Page Application (SPA) estática utilizando React 18, Vite, TypeScript e Tailwind CSS**, rejeitando a adoção do Next.js para este caso de uso.

### Justificativas Técnicas da Decisão

1. **Inexistência de requisito de SEO**: o cockpit é fechado e autenticado; SSR não agrega valor de negócio ao produto.
2. **Eliminação de servidor intermediário desnecessário**: React + Vite produz artefatos estáticos servidos por um proxy reverso **Nginx**, sem um servidor Node.js adicional em produção.
3. **Evitação de conflitos de hidratação**: bibliotecas como `pdfjs-dist` e `react-pdf` dependem de objetos do navegador (`window`, `document`, `HTMLCanvasElement`) e são mais simples de operar diretamente no cliente.
4. **Desempenho e produtividade**: o Vite oferece Hot Module Replacement (HMR) em milissegundos e pipeline de testes nativo com Vitest.

## 4. Consequências e Compensações (Trade-offs)

### Impactos Positivos

- Infraestrutura mais simples e econômica, com um contêiner de runtime a menos na stack Docker.
- Menor atrito no desenvolvimento de recursos visuais complexos de PDF e marcações de evidência.
- Pipeline de CI/CD do frontend rápido, com build estático em menos de 20 segundos.

### Impactos Negativos e Riscos

- O carregamento inicial depende do download do bundle JavaScript; mitigação: code splitting via `React.lazy`, Vite e compressão gzip/Brotli no Nginx.
- O gerenciamento de estado assíncrono e o cache de dados de rede ocorrem no cliente; mitigação: adoção do `@tanstack/react-query`.

## 5. Diretrizes de Implementação e Auditoria

1. O frontend deve permanecer distribuível como artefatos estáticos servidos pelo Nginx.
2. Recursos que dependem de `window`, `document` ou `HTMLCanvasElement` devem ser testados em ambiente de navegador.
3. O CI deve validar o build do frontend, os testes Vitest e o tamanho dos artefatos antes da publicação.

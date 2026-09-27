# Planejamento do Projeto - Visao Geral

**Conform.IA BNDES: Plataforma de Intelligent Document Processing para Verificacao Automatizada de Conformidade**  
*Documento de Direcionamento Estrategico e Tecnico*

---

## Parametros Fundamentais do Projeto

<div class="grid cards" markdown>

- ### Desafio de Referencia
    Consulta Publica BNDES no 01/2025 — Checklist de Conformidade Cadastral, Fiscal, Trabalhista e Regulatoria.

- ### Data de Conclusao
    **07/12/2026** — Execucao organizada em 8 sprints sequenciais de desenvolvimento e validacao.

- ### Modalidade Proposta
    SaaS multi-tenant, conteinerizado em Docker, projetado para hospedagem soberana em territorio nacional.

- ### Publico-Alvo
    Analistas de credito, revisores tecnicos, operadores de compliance e auditores institucionais do BNDES.

</div>

---

## 1. Resumo Executivo

O Conform.IA BNDES responde diretamente ao desafio lancado pelo Banco Nacional de Desenvolvimento Economico e Social (BNDES) na Consulta Publica no 01/2025. O cerne do problema reside em interpretar automaticamente documentos nao estruturados apresentados por empresas proponentes e confrontar informacoes com normativos internos, bases governamentais e sistemas legados de TI.

A solucao adota uma arquitetura de **Intelligent Document Processing (IDP)**, combinando ingestao documental via S3, analise vetorial nativa e OCR Tesseract, motor de regras declarativo em JSON Schema, orquestracao de IA sob o padrao **Maker-Checker**, interface de revisao humana (Human-in-the-Loop) e trilha de auditoria append-only imutavel.

### Objetivos Estrategicos

1. **Eliminacao de Gargalos Manuais**: Reduzir o tempo medio de conferencia documental de dias para segundos por operacao.
2. **Confiabilidade Absoluta**: Garantir tolerancia zero a falsos positivos em certidoes invalidas ou com pendencias fiscais.
3. **Auditabilidade Integral**: Assegurar que qualquer laudo de conformidade seja rastreavel perante orgaos de controle (TCU, CGU).
4. **Governança Agent-First**: Integrar praticas de Harness Engineering para desenvolvimento seguro e verificavel assistido por IA.

---

## 2. Estrutura Modular do Planejamento

Para facilitar a leitura e manutencao, o planejamento oficial esta decomposto nos seguintes capitulos tecnicos:

<div class="grid cards" markdown>

- ### [1. Requisitos e Escopo](requirements.md)
    Detalhamento dos requisitos funcionais RF01 a RF15, requisitos nao funcionais e matriz de dores operacionais.

- ### [2. Arquitetura da Solucao](architecture-design.md)
    Topologia em camadas, selecao tecnologica fundamentada, separacao entre regras e IA e modelo formal de laudo.

- ### [3. Cronograma e Sprints](sprints-roadmap.md)
    Planejamento das 8 sprints ate 07/12/2026, backlog priorizado de epicos (E1 a E10) e Definition of Done.

- ### [4. Seguranca e Governanca](governance-security.md)
    Security by Design, conformidade com a LGPD, matriz de mitigacao de riscos e auditoria transacional.

- ### [5. Harness Engineering](harness-engineering.md)
    Metodologia de contexto delimitado, padrao Maker-Checker, guardrails operacionais e ciclo de trabalho de agentes.

</div>

---

## 3. Premissas e Delimitacao de Escopo

O edital oficial da Consulta Publica no 01/2025 nao disponibiliza amostras de documentos sigilosos de clientes do BNDES, contratos de APIs internas ou regras de negocio confidenciais. 

Por essa razao, o MVP opera com **documentos sinteticos fidedignos e bases simuladas**, mantendo interfaces e adaptadores rigorosamente tipados para que a conexao com sistemas legados do BNDES ocorra de forma transparente na fase de implantacao institucional.

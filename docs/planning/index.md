# Planejamento do Projeto — Visão Geral

**Conform.IA BNDES: Plataforma de Intelligent Document Processing para Verificação Automatizada de Conformidade**
_Documento de Direcionamento Estratégico e Técnico_

---

## Parâmetros Fundamentais do Projeto

<div class="grid cards" markdown>

- ### Desafio de Referência

  Consulta Pública BNDES nº 01/2025 — Checklist de Conformidade Cadastral, Fiscal, Trabalhista e Regulatória.

- ### Data de Conclusão

  **07/12/2026** — Execução organizada em 8 sprints sequenciais de desenvolvimento e validação.

- ### Modalidade Proposta

  SaaS multi-tenant, conteinerizado em Docker, projetado para hospedagem soberana em território nacional.

- ### Público-Alvo
  Analistas de crédito, revisores técnicos, operadores de compliance e auditores institucionais do BNDES.

</div>

---

## 1. Resumo Executivo

O Conform.IA BNDES responde diretamente ao desafio lançado pelo Banco Nacional de Desenvolvimento Econômico e Social (BNDES) na Consulta Pública nº 01/2025. O cerne do problema reside em interpretar automaticamente documentos não estruturados apresentados por empresas proponentes e confrontar informações com normativos internos, bases governamentais e sistemas legados de TI.

A solução adota uma arquitetura de **Intelligent Document Processing (IDP)**, combinando ingestão documental via S3, análise vetorial nativa e OCR Tesseract, motor de regras declarativo em JSON Schema, orquestração de IA sob o padrão **Maker-Checker**, interface de revisão humana (Human-in-the-Loop) e trilha de auditoria append-only imutável.

### Objetivos Estratégicos

1. **Eliminação de Gargalos Manuais**: Reduzir o tempo médio de conferência documental de dias para segundos por operação.
2. **Confiabilidade Absoluta**: Garantir tolerância zero a falsos positivos em certidões inválidas ou com pendências fiscais.
3. **Auditabilidade Integral**: Assegurar que qualquer laudo de conformidade seja rastreável perante órgãos de controle (TCU, CGU).
4. **Governança Agent-First**: Integrar práticas de Harness Engineering para desenvolvimento seguro e verificável assistido por IA.

---

## 2. Estrutura Modular do Planejamento

Para facilitar a leitura e manutenção, o planejamento oficial esta decomposto nos seguintes capitulos técnicos:

<div class="grid cards" markdown>

- ### [1. Requisitos e Escopo](requirements.md)

  Detalhamento dos requisitos funcionais RF01 a RF15, requisitos não funcionais e matriz de dores operacionais.

- ### [2. Arquitetura da Solução](architecture-design.md)

  Topologia em camadas, seleção tecnologica fundamentada, separação entre regras e IA e modelo formal de laudo.

- ### [3. Cronograma e Sprints](sprints-roadmap.md)

  Planejamento das 8 sprints até 07/12/2026, backlog priorizado de epicos (E1 a E10) e Definition of Done.

- ### [4. Segurança e Governança](governance-security.md)

  Security by Design, conformidade com a LGPD, matriz de mitigação de riscos e auditoria transacional.

- ### [5. Harness Engineering](harness-engineering.md)
  Metodologia de contexto delimitado, padrão Maker-Checker, guardrails operacionais e ciclo de trabalho de agentes.

</div>

---

## 3. Premissas e Delimitação de Escopo

O edital oficial da Consulta Publica no 01/2025 não disponibiliza amostras de documentos sigilosos de clientes do BNDES, contratos de APIs internas ou regras de negócio confidenciais.

Por essa razão, o MVP opera com **documentos sintéticos fidedignos e bases simuladas**, mantendo interfaces e adaptadores rigorosamente tipados para que a conexão com sistemas legados do BNDES ocorra de forma transparente na fase de implantação institucional.

# Visão Geral do Produto

**Conform.IA BNDES: Plataforma de Intelligent Document Processing para Verificação Automatizada de Conformidade**
_Documento de Direcionamento Estratégico e Técnico_

---

## Parâmetros Fundamentais do Projeto

<div class="grid cards" markdown>

- ### Desafio de Referência

    Consulta Pública BNDES nº 01/2025 — Checklist de Conformidade Cadastral, Fiscal, Trabalhista e Regulatória.

- ### Data de Conclusão

    **05/12/2026** — Milestones M1 a M6, detalhados no [Plano de Entrega](DELIVERY_PLAN_2026_12_05.md).

- ### Modalidade Proposta

    Aplicação conteinerizada em Docker, sem dependência de nuvem estrangeira para o processamento dos documentos (exceto o LLM opcional das regras híbridas).

- ### Público-Alvo
    Analistas de crédito, revisores técnicos, operadores de compliance e auditores institucionais do BNDES.

</div>

---

## 1. Resumo Executivo

O Conform.IA BNDES responde diretamente ao desafio lançado pelo Banco Nacional de Desenvolvimento Econômico e Social (BNDES) na Consulta Pública nº 01/2025. O cerne do problema reside em interpretar automaticamente documentos não estruturados apresentados por empresas proponentes e confrontar informações com normativos internos, bases governamentais e sistemas legados de TI.

A solução adota uma arquitetura de **Intelligent Document Processing (IDP)**, combinando ingestão documental via S3, análise vetorial nativa e OCR Tesseract, motor de regras declarativo em JSON Schema, orquestração de IA sob o padrão **Maker-Checker**, interface de revisão humana (Human-in-the-Loop) e trilha de auditoria append-only imutável.

### Objetivos Estratégicos

1. **Menos conferência manual**: Automatizar a verificação das certidões mais frequentes e deixar ao analista apenas os casos com dúvida.
2. **Nenhuma aprovação indevida**: Tolerância zero a falsos positivos em certidões inválidas ou com pendências, verificada no CI.
3. **Auditabilidade Integral**: Assegurar que qualquer laudo de conformidade seja rastreável perante órgãos de controle (TCU, CGU).
4. **Governança Agent-First**: Integrar práticas de Harness Engineering para desenvolvimento seguro e verificável assistido por IA.

---

## 2. Estrutura Modular do Planejamento

Para aprofundar, siga para os capítulos:

<div class="grid cards" markdown>

- ### [Requisitos e Escopo](requirements.md)

    Requisitos funcionais RF01 a RF15, requisitos não funcionais e jornada do analista.

- ### [Arquitetura](../architecture/overview.md)

    Serviços, fluxo de processamento, separação entre regras e IA e modelo de dados.

- ### [Plano de Entrega](DELIVERY_PLAN_2026_12_05.md)

    Escopo do MVP, caminho crítico, cronograma até 05/12/2026 e critérios de Go/No-Go.

- ### [Segurança, LGPD e Auditoria](governance-security.md)

    Controles implementados, trilha de auditoria, riscos e pendências para produção.

- ### [Maker-Checker e Guardrails](../engineering/maker-checker.md)

    Como a IA participa da decisão sem poder aprovar sozinha.

</div>

---

## 3. Premissas e Delimitação de Escopo

O edital oficial da Consulta Pública nº 01/2025 não disponibiliza amostras de documentos sigilosos de clientes do BNDES, contratos de APIs internas ou regras de negócio confidenciais.

Por essa razão, o MVP opera com **documentos sintéticos fidedignos e bases simuladas**, mantendo interfaces e adaptadores rigorosamente tipados para que a conexão com sistemas legados do BNDES ocorra de forma transparente na fase de implantação institucional.

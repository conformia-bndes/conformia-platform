# Cronograma de Sprints e Backlog de Épicos

!!! warning "Documento histórico"
    Planejamento elaborado no início do projeto, mantido como registro. O escopo, as datas e o
    estado atual estão no [Plano de Entrega](DELIVERY_PLAN_2026_12_05.md), no
    [Backlog](IMPLEMENTATION_BACKLOG.md) e no [Relatório de Validação](VALIDATION_REPORT.md).
    A data de entrega adotada é **05/12/2026**.

Este documento detalha o planejamento operacional das 8 sprints de desenvolvimento da plataforma Conform.IA BNDES até a data final de encerramento em **07/12/2026**, incluindo o catálogo de épicos e a Definition of Done (DoD) formal.

---

## 1. Cronograma Geral das Sprints (Setembro a Dezembro de 2026)

| Sprint       | Período       | Foco Estratégico                | Objetivos Principais                                                                                                            | Entregável Consolidado                                                                                     |
| :----------- | :------------ | :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------- |
| **Sprint 1** | 15/09 – 25/09 | **Fundação e Descoberta**       | Setup de monorepo, Docker Compose oficial, governança sem emojis, documentação inicial, toolchain Astral `uv` e baseline de CI. | <span class="badge badge-compliant">Concluída</span> Ambiente reproduzível e CI aprovado.                  |
| **Sprint 2** | 26/09 – 06/10 | **Ingestão Documental**         | Upload de documentos, integração MinIO S3, processamento assíncrono Celery e pipeline vetorial/OCR Tesseract.                   | <span class="badge badge-info">Em Andamento</span> Documento ingerido gerando texto e metadados.           |
| **Sprint 3** | 07/10 – 17/10 | **Extração Estruturada**        | Normalização de entidades (CNPJ, datas de validade), tabelas e citações de evidências em esquemas JSON Schema e Pydantic.       | <span class="badge badge-review">Planejada</span> JSON estruturado com índices de confiança e coordenadas. |
| **Sprint 4** | 18/10 – 31/10 | **Checklist e Regras**          | Motor de regras determinísticas, validação temporal de certidões, detecção de falência e aplicação do checklist normativo.      | <span class="badge badge-review">Planejada</span> Checklist executável e geração de laudo preliminar.      |
| **Sprint 5** | 01/11 – 14/11 | **IA e Explicabilidade**        | Integração com LLMs sob padrão Maker-Checker, análise de cláusulas e geração de justificativas técnicas contextuais.            | <span class="badge badge-review">Planejada</span> Pipeline híbrido regras + IA sem alucinações.            |
| **Sprint 6** | 15/11 – 24/11 | **Interface e Revisão**         | Painel operacional React, visualizador split-view documento/evidências, fluxo de contestação, exceções e relatório PDF.         | <span class="badge badge-review">Planejada</span> Fluxo ponta a ponta utilizável pelo analista BNDES.      |
| **Sprint 7** | 25/11 – 01/12 | **Segurança e Observabilidade** | Autenticação RBAC, políticas de segurança estritas, traces OpenTelemetry, testes de carga e sanitização LGPD.                   | <span class="badge badge-review">Planejada</span> Release Candidate homologada para demonstração.          |
| **Sprint 8** | 02/12 – 07/12 | **Validação e Entrega**         | Execução de benchmarks finais, revisão integral da documentação, vídeo demonstrativo e entrega oficial do MVP.                  | <span class="badge badge-review">Planejada</span> MVP final entregue, demonstrado e auditável.             |

---

## 2. Catálogo de Épicos (E1 a E10)

<div class="grid cards" markdown>

- ### E1 — Gestão Documental

  Ingestão, validação de magic bytes (`%PDF-`), armazenamento durável no MinIO S3, catálogo de metadados e ciclo de vida de arquivos.

- ### E2 — Pipeline IDP Híbrido

  Extração vetorial nativa de PDFs com pdfplumber e chaveamento automático para OCR Tesseract 5 em páginas digitalizadas.

- ### E3 — Checklist Declarativo

  Estruturação e versionamento de normas e critérios de conformidade em formato JSON Schema desacoplado do código-fonte.

- ### E4 — Motor de Regras Determinístico

  Processamento booleano e temporal de restrições cadastrais, fiscais e financeiras com tolerância zero a divergências.

- ### E5 — Orquestração de IA Maker-Checker

  Avaliação semântica assistida por modelos de linguagem com citação literal obrigatória de evidências factuais.

- ### E6 — Camada de Conectores

  Adaptadores desacoplados para integração com bases governamentais e APIs corporativas do BNDES.

- ### E7 — Revisão Humana (HITL)

  Interface operacional para análise de apontamentos, confirmação de laudos, contestação e deferimento de exceções motivadas.

- ### E8 — Trilha de Auditoria Imutável

  Registro transacional cronológico (`append-only`) de todas as etapas de análise, timestamps UTC e identificadores de agentes.

- ### E9 — Analytics e Qualidade

  Dashboard de métricas de desempenho, acurácia geral, recall de extração, Character Error Rate (CER) e taxas de revisão.

- ### E10 — Segurança e Governança
  Controle de acesso baseado em papeis (RBAC), conformidade estrita com a LGPD, gestão segura de credenciais e CI com SAST.

</div>

---

## 3. Definition of Done (DoD) Formal

Nenhuma funcionalidade, commit ou pull request e considerado concluido sem atender integralmente aos seguintes requisitos:

1. **Revisão de Código**: Mudanças integradas ao monorepo de acordo com as diretrizes do `CONTRIBUTING.md` e revisadas tecnicamente.
2. **Suite de Testes**: Testes automatizados (`pytest`, `vitest`) passando integralmente com cobertura mínima de 70%.
3. **Harness Evals Aprovado**: Benchmark de avaliação continua (`python evals/eval_pipeline.py`) aprovado com 100% de acerto e 0 falsos positivos.
4. **Linters e Formatação**: Verificações com `black --check`, `flake8` e `npm run lint` concluidas sem nenhuma advertência.
5. **Segurança Aprovada**: Escaneamento de segredos com `gitleaks` e auditoria de vulnerabilidades com `pip-audit` sem apontamentos.
6. **Documentação Sincronizada**: Atualização imediata das páginas relevantes no MkDocs e no README.
7. **Política Estilistica**: **Proibição absoluta do uso de emojis** em códigos, testes, documentação e mensagens de commit.

---

## 4. Cenário de Demonstração Mínima do MVP

Para a demonstração técnica conclusiva perante o BNDES em 07/12/2026, o cenário operacional mínimo homologado compreende:

```text
[Analista autentica no sistema]
            │
            ▼
[Upload de PDF de CND Federal / CRF FGTS]
            │
            ▼
[Extracao automatica vetorial + OCR Tesseract]
            │
            ▼
[Execucao do Checklist Normativo BNDES 2025]
            │
            ▼
[Maker-Checker valida evidencias textuais]
            │
            ▼
[Apresentacao de laudo com destaque literal]
            │
            ▼
[Intervencao do analista com parecer de excecao]
            │
            ▼
[Gravacao na Trilha de Auditoria e emissao de laudo PDF]
```

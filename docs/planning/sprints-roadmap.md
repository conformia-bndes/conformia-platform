# Cronograma de Sprints e Backlog de Epicos

Este documento detalha o planejamento operacional das 8 sprints de desenvolvimento da plataforma Conform.IA BNDES ate a data final de encerramento em **07/12/2026**, incluindo o catalogo de epicos e a Definition of Done (DoD) formal.

---

## 1. Cronograma Geral das Sprints (Setembro a Dezembro de 2026)

| Sprint       | Periodo       | Foco Estrategico                | Objetivos Principais                                                                                                            | Entregavel Consolidado                                                                                     |
| :----------- | :------------ | :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------- |
| **Sprint 1** | 15/09 – 25/09 | **Fundação e Descoberta**       | Setup de monorepo, Docker Compose oficial, governança sem emojis, documentação inicial, toolchain Astral `uv` e baseline de CI. | <span class="badge badge-compliant">Concluída</span> Ambiente reproduzível e CI aprovado.                  |
| **Sprint 2** | 26/09 – 06/10 | **Ingestão Documental**         | Upload de documentos, integração MinIO S3, processamento assíncrono Celery e pipeline vetorial/OCR Tesseract.                   | <span class="badge badge-info">Em Andamento</span> Documento ingerido gerando texto e metadados.           |
| **Sprint 3** | 07/10 – 17/10 | **Extracao Estruturada**        | Normalizacao de entidades (CNPJ, datas de validade), tabelas e citacoes de evidencias em esquemas JSON Schema e Pydantic.       | <span class="badge badge-review">Planejada</span> JSON estruturado com indices de confianca e coordenadas. |
| **Sprint 4** | 18/10 – 31/10 | **Checklist e Regras**          | Motor de regras determinísticas, validação temporal de certidões, detecção de falência e aplicação do checklist normativo.      | <span class="badge badge-review">Planejada</span> Checklist executável e geração de laudo preliminar.      |
| **Sprint 5** | 01/11 – 14/11 | **IA e Explicabilidade**        | Integração com LLMs sob padrão Maker-Checker, análise de cláusulas e geração de justificativas técnicas contextuais.            | <span class="badge badge-review">Planejada</span> Pipeline híbrido regras + IA sem alucinações.            |
| **Sprint 6** | 15/11 – 24/11 | **Interface e Revisao**         | Painel operacional React, visualizador split-view documento/evidencias, fluxo de contestacao, excecoes e relatorio PDF.         | <span class="badge badge-review">Planejada</span> Fluxo ponta a ponta utilizavel pelo analista BNDES.      |
| **Sprint 7** | 25/11 – 01/12 | **Segurança e Observabilidade** | Autenticação RBAC, políticas de segurança estritas, traces OpenTelemetry, testes de carga e sanitização LGPD.                   | <span class="badge badge-review">Planejada</span> Release Candidate homologada para demonstração.          |
| **Sprint 8** | 02/12 – 07/12 | **Validacao e Entrega**         | Execucao de benchmarks finais, revisao integral da documentacao, video demonstrativo e entrega oficial do MVP.                  | <span class="badge badge-review">Planejada</span> MVP final entregue, demonstrado e auditavel.             |

---

## 2. Catalogo de Epicos (E1 a E10)

<div class="grid cards" markdown>

- ### E1 — Gestao Documental

  Ingestao, validacao de magic bytes (`%PDF-`), armazenamento duravel no MinIO S3, catalogo de metadados e ciclo de vida de arquivos.

- ### E2 — Pipeline IDP Hibrido

  Extracao vetorial nativa de PDFs com pdfplumber e chaveamento automatico para OCR Tesseract 5 em paginas digitalizadas.

- ### E3 — Checklist Declarativo

  Estruturacao e versionamento de normas e criterios de conformidade em formato JSON Schema desacoplado do codigo-fonte.

- ### E4 — Motor de Regras Determinístico

  Processamento booleano e temporal de restricoes cadastrais, fiscais e financeiras com tolerancia zero a divergencias.

- ### E5 — Orquestracao de IA Maker-Checker

  Avaliacao semantica assistida por modelos de linguagem com citacao literal obrigatoria de evidencias factuais.

- ### E6 — Camada de Conectores

  Adaptadores desacoplados para integracao com bases governamentais e APIs corporativas do BNDES.

- ### E7 — Revisao Humana (HITL)

  Interface operacional para analise de apontamentos, confirmacao de laudos, contestacao e deferimento de excecoes motivadas.

- ### E8 — Trilha de Auditoria Imutavel

  Registro transacional cronologico (`append-only`) de todas as etapas de analise, timestamps UTC e identificadores de agentes.

- ### E9 — Analytics e Qualidade

  Dashboard de metricas de desempenho, acuracia geral, recall de extracao, Character Error Rate (CER) e taxas de revisao.

- ### E10 — Seguranca e Governanca
  Controle de acesso baseado em papeis (RBAC), conformidade estrita com a LGPD, gestao segura de credenciais e CI com SAST.

</div>

---

## 3. Definition of Done (DoD) Formal

Nenhuma funcionalidade, commit ou pull request e considerado concluido sem atender integralmente aos seguintes requisitos:

1. **Revisao de Codigo**: Mudancas integradas ao monorepo de acordo com as diretrizes do `CONTRIBUTING.md` e revisadas tecnicamente.
2. **Suite de Testes**: Testes automatizados (`pytest`, `vitest`) passando integralmente com cobertura minima de 70%.
3. **Harness Evals Aprovado**: Benchmark de avaliacao continua (`python evals/eval_pipeline.py`) aprovado com 100% de acerto e 0 falsos positivos.
4. **Linters e Formatacao**: Verificacoes com `black --check`, `flake8` e `npm run lint` concluidas sem nenhuma advertencia.
5. **Seguranca Aprovada**: Escaneamento de segredos com `gitleaks` e auditoria de vulnerabilidades com `pip-audit` sem apontamentos.
6. **Documentacao Sincronizada**: Atualizacao imediata das paginas relevantes no MkDocs e no README.
7. **Politica Estilistica**: **Proibicao absoluta do uso de emojis** em codigos, testes, documentacao e mensagens de commit.

---

## 4. Cenario de Demonstracao Minima do MVP

Para a demonstracao tecnica conclusiva perante o BNDES em 07/12/2026, o cenario operacional minimo homologado compreende:

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

# Seguranca, LGPD, Governanca e Auditoria

Este documento consolida as diretrizes de seguranca da informacao, protecao de dados pessoais (LGPD), gestao de riscos e auditoria transacional da plataforma Conform.IA BNDES.

---

## 1. Principios de Seguranca e Privacidade

A plataforma opera sob os principios estritos de **Security by Design** e **Privacy by Design**:

- **Minimizacao de Dados**: O sistema processa estritamente os campos necessarios a comprovacao de regularidade cadastral e documental exigida pelo BNDES.
- **Isolamento de Credenciais**: Segredos, tokens e chaves de conexao sao gerenciados exclusivamente fora do repositorio, via variaveis de ambiente auditadas por ferramentas SAST.
- **Criptografia de Ponta a Ponta**: Trafego protegido por TLS 1.3 em transito e dados em repouso armazenados em volumes protegidos no PostgreSQL e MinIO.
- **Segregacao de Ambientes**: O ambiente de desenvolvimento utiliza exclusivamente documentos sinteticos, sem presenca de dados reais de clientes ou proponentes do BNDES.

---

## 2. Matriz de Gestao de Riscos e Mitigacao

| Risco Tecnico ou Operacional | Severidade | Impacto | Estrategia de Mitigacao Implementada |
| :--- | :--- | :--- | :--- |
| **Alucinacao de modelo de IA** | Critica | Aprovacao indevida de certidao com debitos ativos. | Padrao **Maker-Checker** compulsorio: citacao literal exata da evidencia e verificacao deterministica antes de qualquer aprovacao. |
| **Degradacao de OCR em certidoes digitalizadas** | Alta | Falha na extracao de datas de validade ou CNPJ. | Pre-processamento de imagem, binarizacao adaptativa e exigencia de status `MANUAL_REVIEW_REQUIRED` quando a confianca for baixa. |
| **Vazamento de PII ou violacao da LGPD** | Critica | Sancoes administrativas e quebra de sigilo bancario. | Sanitizacao de traces e logs (OpenTelemetry sem CPF ou dados bancarios), minimizacao de dados e destruicao controlada. |
| **Ambiguidade em normas e editais** | Alta | Divergencia interpretativa entre analistas e modelos. | Regras declarativas em JSON Schema versionado, revisadas tecnicamente e cobertas por testes de regressao. |
| **Indisponibilidade de APIs governamentais** | Media | Paralizacao de esteiras de verificacao de credito. | Arquitetura desacoplada via adaptadores e filas de re-tentativa com backoff exponencial no Celery. |

---

## 3. Trilha de Auditoria Transacional (`audit_logs`)

Para garantir a prestacao de contas e a conformidade perante orgaos de fiscalizacao e controle (Tribunal de Contas da Uniao - TCU e Controladoria-Geral da Uniao - CGU), nenhuma decisao automatizada ou humana pode ser opaca ou efemera.

### Estrutura do Snapshot de Auditoria

Toda avaliacao gera um registro imutavel no PostgreSQL contendo:

1. **Identificador Unico da Avaliacao** (`report_id` UUID).
2. **Hash Criptografico do Arquivo** (`sha256` do PDF original analisado).
3. **Versao Normativa da Regra** (versao exata do checklist em `rules/schemas/`).
4. **Citacao Literal da Evidencia** (trecho textual exato, numero da pagina e coordenadas).
5. **Agente ou Usuario Executor** (identificador do processo automatizado ou do analista humano).
6. **Timestamp UTC Imutavel** (data e hora exata da deliberacao).
7. **Parecer Tecnico Consolidado** (justificativa tecnica e situacao de deferimento/indeferimento).

---

## 4. Tratamento Formal de Excecoes

No contexto de concessoes de credito publico, **uma excecao nunca significa ignorar uma regra**.

Quando uma certidao apresenta ressalva amparada por decisao judicial liminar ou autorizacao formal da diretoria do BNDES:

- O sistema mantem o historico da nao conformidade original registrada.
- O analista humano insere um parecer circunstanciado informando o numero do processo judicial ou termo de autorizacao.
- O status da regra e alterado para `EXCEPTION_AUTHORIZED`.
- O registro de auditoria armazena simultaneamente o laudo tecnico original da IA e a motivacao formal da excecao humana.

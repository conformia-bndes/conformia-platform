# Segurança, LGPD, Governança e Auditoria

Este documento consolida as diretrizes de segurança da informação, proteção de dados pessoais (LGPD), gestão de riscos e auditoria transacional da plataforma Conform.IA BNDES.

---

## 1. Princípios de Segurança e Privacidade

A plataforma opera sob os principios estritos de **Security by Design** e **Privacy by Design**:

- **Minimização de Dados**: O sistema processa estritamente os campos necessários a comprovação de regularidade cadastral e documental exigida pelo BNDES.
- **Isolamento de Credenciais**: Segredos, tokens e chaves de conexão são gerenciados exclusivamente fora do repositório, via variáveis de ambiente auditadas por ferramentas SAST.
- **Criptografia de Ponta a Ponta**: Trafego protegido por TLS 1.3 em trânsito e dados em repouso armazenados em volumes protegidos no PostgreSQL e MinIO.
- **Segregação de Ambientes**: O ambiente de desenvolvimento utiliza exclusivamente documentos sintéticos, sem presença de dados reais de clientes ou proponentes do BNDES.

---

## 2. Matriz de Gestão de Riscos e Mitigação

| Risco Técnico ou Operacional                     | Severidade | Impacto                                               | Estratégia de Mitigação Implementada                                                                                               |
| :----------------------------------------------- | :--------- | :---------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| **Alucinação de modelo de IA**                   | Critica    | Aprovação indevida de certidão com débitos ativos.    | Padrão **Maker-Checker** compulsório: citação literal exata da evidência e verificação determinística antes de qualquer aprovação. |
| **Degradação de OCR em certidões digitalizadas** | Alta       | Falha na extração de datas de validade ou CNPJ.       | Pre-processamento de imagem, binarização adaptativa e exigência de status `MANUAL_REVIEW_REQUIRED` quando a confiança for baixa.   |
| **Vazamento de PII ou violação da LGPD**         | Critica    | Sanções administrativas e quebra de sigilo bancário.  | Sanitização de traces e logs (OpenTelemetry sem CPF ou dados bancários), minimização de dados e destruição controlada.             |
| **Ambiguidade em normas e editais**              | Alta       | Divergência interpretativa entre analistas e modelos. | Regras declarativas em JSON Schema versionado, revisadas tecnicamente e cobertas por testes de regressão.                          |
| **Indisponibilidade de APIs governamentais**     | Media      | Paralisação de esteiras de verificação de crédito.    | Arquitetura desacoplada via adaptadores e filas de re-tentativa com backoff exponencial no Celery.                                 |

---

## 3. Trilha de Auditoria Transacional (`audit_logs`)

Para garantir a prestação de contas e a conformidade perante órgãos de fiscalização e controle (Tribunal de Contas da União — TCU e Controladoria-Geral da União — CGU), nenhuma decisão automatizada ou humana pode ser opaca ou efêmera.

### Estrutura do Snapshot de Auditoria

Toda avaliação gera um registro imutável no PostgreSQL contendo:

1. **Identificador Único da Avaliação** (`report_id` UUID).
2. **Hash Criptografico do Arquivo** (`sha256` do PDF original analisado).
3. **Versão Normativa da Regra** (versão exata do checklist em `rules/schemas/`).
4. **Citação Literal da Evidência** (trecho textual exato, número da página e coordenadas).
5. **Agente ou Usuário Executor** (identificador do processo automatizado ou do analista humano).
6. **Timestamp UTC Imutável** (data e hora exata da deliberação).
7. **Parecer Técnico Consolidado** (justificativa técnica e situação de deferimento/indeferimento).

---

## 4. Tratamento Formal de Exceções

No contexto de concessões de crédito público, **uma exceção nunca significa ignorar uma regra**.

Quando uma certidão apresenta ressalva amparada por decisão judicial liminar ou autorização formal da diretoria do BNDES:

- O sistema mantem o histórico da não conformidade original registrada.
- O analista humano insere um parecer circunstanciado informando o número do processo judicial ou termo de autorização.
- O status da regra e alterado para `EXCEPTION_AUTHORIZED`.
- O registro de auditoria armazena simultaneamente o laudo técnico original da IA e a motivação formal da exceção humana.

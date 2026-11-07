# Política de Segurança da Informação - Conform.IA BNDES

A segurança da informação e a integridade de dados são pilares críticos do Conform.IA BNDES. Por atuar na esteira de verificação de conformidade para concessões de crédito e investimentos com recursos públicos federais, vulnerabilidades são tratadas com a mais alta prioridade técnica e institucional.

---

## 1. Versões Suportadas

Atualizações e patches de segurança são fornecidos para as seguintes versões:

| Versão | Status de Suporte |
| :--- | :--- |
| >= 0.1.x | Suportada |
| < 0.1.0 | Não suportada |

---

## 2. Como Reportar uma Vulnerabilidade de Segurança

Não registre Issues públicas no GitHub para reportar vulnerabilidades de segurança. A divulgação prematura pode expor a plataforma a riscos antes da disponibilização de mitigações ou correções.

Para reportar uma vulnerabilidade:
1. Utilize o canal oficial de [Reporte Privado de Vulnerabilidades do GitHub](https://github.com/conformia-bndes/conformia-platform/security/advisories/new).
2. Forneca uma descrição detalhada contendo:
   - Componente afetado (ex: Pipeline IDP, Motor de Regras, Armazenamento MinIO, Trilha de Auditoria).
   - Passos reprodutiveis ou prova de conceito (PoC).
   - Avaliação de impacto e sugestao de mitigação técnica, quando aplicável.

---

## 3. Prazos e Niveis de Serviço (SLA) de Resposta

| Etapa do Processo | Prazo Limite |
| :--- | :--- |
| Confirmação de recebimento do reporte | Ate 24 horas uteis |
| Triagem técnica e classificação CVSS | Ate 3 dias uteis |
| Desenvolvimento e homologação de patch | Variável conforme severidade (Crítica: ate 48h) |
| Publicação coordenada de segurança | Apos deploy da correção em produção |

---

## 4. Escopo de Segurança do Projeto

Estão formalmente dentro do escopo desta política:
- Proteção contra execução remota de código e explorações em parsers de PDF/OCR (Poppler, Tesseract).
- Prevenção de Path Traversal e injeção de arquivos no upload documental.
- Integridade e inviolabilidade dos registros da trilha de auditoria (`audit_logs`).
- Prevenção de vazamento de Dados Pessoais Sensíveis (LGPD / PII) em logs e traces.
- Resiliência do validador Maker-Checker contra técnicas de injeção de prompt (Prompt Injection) voltadas a aprovar certidões fraudulentas.

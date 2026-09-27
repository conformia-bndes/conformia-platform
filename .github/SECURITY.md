# Politica de Seguranca da Informacao - Conform.IA BNDES

A seguranca da informacao e a integridade de dados sao pilares criticos do Conform.IA BNDES. Por atuar na esteira de verificacao de conformidade para concessoes de credito e investimentos com recursos publicos federais, vulnerabilidades sao tratadas com a mais alta prioridade tecnica e institucional.

---

## 1. Versoes Suportadas

Atualizacoes e patches de seguranca sao fornecidos para as seguintes versoes:

| Versao | Status de Suporte |
| :--- | :--- |
| >= 0.1.x | Suportada |
| < 0.1.0 | Nao suportada |

---

## 2. Como Reportar uma Vulnerabilidade de Seguranca

Nao registre Issues publicas no GitHub para reportar vulnerabilidades de seguranca. A divulgacao prematura pode expor a plataforma a riscos antes da disponibilizacao de mitigacoes ou correcoes.

Para reportar uma vulnerabilidade:
1. Utilize o canal oficial de [Reporte Privado de Vulnerabilidades do GitHub](https://github.com/conformia-bndes/conformia-platform/security/advisories/new).
2. Forneca uma descricao detalhada contendo:
   - Componente afetado (ex: Pipeline IDP, Motor de Regras, Armazenamento MinIO, Trilha de Auditoria).
   - Passos reprodutiveis ou prova de conceito (PoC).
   - Avaliacao de impacto e sugestao de mitigacao tecnica, quando aplicavel.

---

## 3. Prazos e Niveis de Servico (SLA) de Resposta

| Etapa do Processo | Prazo Limite |
| :--- | :--- |
| Confirmacao de recebimento do reporte | Ate 24 horas uteis |
| Triagem tecnica e classificacao CVSS | Ate 3 dias uteis |
| Desenvolvimento e homologacao de patch | Variavel conforme severidade (Critica: ate 48h) |
| Publicacao coordenada de seguranca | Apos deploy da correcao em producao |

---

## 4. Escopo de Seguranca do Projeto

Estao formalmente dentro do escopo desta politica:
- Protecao contra execucao remota de codigo e exploracoes em parsers de PDF/OCR (Poppler, Tesseract).
- Prevencao de Path Traversal e injecao de arquivos no upload documental.
- Integridade e inviolabilidade dos registros da trilha de auditoria (`audit_logs`).
- Prevencao de vazamento de Dados Pessoais Sensiveis (LGPD / PII) em logs e traces.
- Resiliencia do validador Maker-Checker contra tecnicas de injecao de prompt (Prompt Injection) voltadas a aprovar certidoes fraudulentas.

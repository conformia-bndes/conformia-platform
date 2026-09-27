# Matriz de Conformidade — Consulta Pública BNDES 01/2025

Este documento detalha o mapeamento normativo e os critérios de verificação automatizada de admissibilidade documental para proponentes de operações de crédito e financiamento no BNDES, fundamentado na **Consulta Pública nº 01/2025**.

---

## 1. Fundamentação Legal e Objetivos

O processo de concessão de apoio financeiro pelo BNDES requer a estrita observância da legislação federal, resoluções do Conselho Monetário Nacional (CMN) e políticas operacionais internas do Banco. A presença de qualquer irregularidade cadastral, fiscal, trabalhista ou de idoneidade veda categoricamente a celebração do contrato de financiamento.

---

## 2. Matriz de Requisitos e Regras Normativas

| Codigo da Regra    | Requisito Normativo                         | Base Legal                                                   | Tipo de Validacao       | Criterio de Aprovacao                                                                 | Acao em Falha                                                   |
| :----------------- | :------------------------------------------ | :----------------------------------------------------------- | :---------------------- | :------------------------------------------------------------------------------------ | :-------------------------------------------------------------- |
| **RULE-BNDES-001** | Regularidade Fiscal Perante a Uniao (CND)   | Decreto-Lei no 147/1967; Lei no 8.212/1991, art. 47          | Deterministica          | Certidao Negativa valida ou Certidao Positiva com Efeito de Negativa vigente          | Bloqueio imediato (`NON_COMPLIANT`)                             |
| **RULE-BNDES-002** | Regularidade de FGTS (CRF Caixa)            | Lei no 8.036/1990, art. 27                                   | Deterministica          | Certificado de Regularidade com status "SITUACAO REGULAR" e data vigente              | Bloqueio imediato (`NON_COMPLIANT`)                             |
| **RULE-BNDES-003** | Inexistencia de Debitos Trabalhistas (CNDT) | Lei no 12.440/2011; Art. 642-A da CLT                        | Deterministica          | Certidao emitida pelo Tribunal Superior do Trabalho sem apontamentos ativos           | Bloqueio imediato (`NON_COMPLIANT`)                             |
| **RULE-BNDES-004** | Inexistencia de Processo Falimentar         | Lei no 11.101/2005                                           | Hibrida (Maker-Checker) | Certidao dos Distribuidores Civeis atestando "Nada Consta" de falencia ou recuperacao | Encaminhamento para analise juridica (`MANUAL_REVIEW_REQUIRED`) |
| **RULE-BNDES-005** | Regularidade / Licenciamento Ambiental      | Resolucao CMN no 4.327/2014; Politica Socioambiental BNDES   | Hibrida (Maker-Checker) | Licenca ambiental de operacao valida para a atividade ou dispensa formal comprovada   | Bloqueio ou revisao tecnica (`MANUAL_REVIEW_REQUIRED`)          |
| **RULE-BNDES-006** | Idoneidade e Transparencia (CEIS / CNEP)    | Lei no 12.846/2013 (Anticorrupcao); Diretrizes de Compliance | Deterministica          | Ausencia de inscricao nos cadastros de empresas inidoneas e suspensas                 | Bloqueio imediato (`NON_COMPLIANT`)                             |

---

## 3. Politica de Tolerancia Zero e Classificacao de Risco

1. **Infracoes Criticas**: Débitos tributarios com a Fazenda Nacional ou inscricao ativa no CEIS/CNEP resultam em reprovacao sumaria do dossie sem possibilidade de sobrestamento pelo motor de regras.
2. **Casos Ambiguos e Baixa Qualidade de Imagem**: Documentos com carimbos ilegiveis ou corte de margem acionam o protocolo de degradacao para revisao manual, impedindo a aprovacao indevida por omissao de dados.
3. **Imutabilidade do Laudo**: Todo parecer gerado pelo motor de regras e gravado com chave estrangeira para o documento original, registrando o estado das regras no instante da verificacao.

# Matriz de Conformidade — Consulta Pública BNDES 01/2025

Este documento detalha o mapeamento normativo e os critérios de verificação automatizada de admissibilidade documental para proponentes de operações de crédito e financiamento no BNDES, fundamentado na **Consulta Pública nº 01/2025**.

---

## 1. Fundamentação Legal e Objetivos

O processo de concessão de apoio financeiro pelo BNDES requer a estrita observância da legislação federal, resoluções do Conselho Monetário Nacional (CMN) e políticas operacionais internas do Banco. A presença de qualquer irregularidade cadastral, fiscal, trabalhista ou de idoneidade veda categoricamente a celebração do contrato de financiamento.

---

## 2. Matriz de Requisitos e Regras Normativas

| Código da Regra    | Requisito Normativo                         | Base Legal                                                   | Tipo de Validação       | Critério de Aprovação                                                                 | Ação em Falha                                                   |
| :----------------- | :------------------------------------------ | :----------------------------------------------------------- | :---------------------- | :------------------------------------------------------------------------------------ | :-------------------------------------------------------------- |
| **RULE-BNDES-001** | Regularidade Fiscal Perante a União (CND)   | Decreto-Lei no 147/1967; Lei no 8.212/1991, art. 47          | Determinística          | Certidão Negativa valida ou Certidão Positiva com Efeito de Negativa vigente          | Bloqueio imediato (`NON_COMPLIANT`)                             |
| **RULE-BNDES-002** | Regularidade de FGTS (CRF Caixa)            | Lei no 8.036/1990, art. 27                                   | Determinística          | Certificado de Regularidade com status "SITUAÇÃO REGULAR" e data vigente              | Bloqueio imediato (`NON_COMPLIANT`)                             |
| **RULE-BNDES-003** | Inexistência de Débitos Trabalhistas (CNDT) | Lei no 12.440/2011; Art. 642-A da CLT                        | Determinística          | Certidão emitida pelo Tribunal Superior do Trabalho sem apontamentos ativos           | Bloqueio imediato (`NON_COMPLIANT`)                             |
| **RULE-BNDES-004** | Inexistência de Processo Falimentar         | Lei no 11.101/2005                                           | Híbrida (Maker-Checker) | Certidão dos Distribuidores Cíveis atestando "Nada Consta" de falência ou recuperação | Encaminhamento para análise jurídica (`MANUAL_REVIEW_REQUIRED`) |
| **RULE-BNDES-005** | Regularidade / Licenciamento Ambiental      | Resolução CMN no 4.327/2014; Política Socioambiental BNDES   | Híbrida (Maker-Checker) | Licença ambiental de operação valida para a atividade ou dispensa formal comprovada   | Bloqueio ou revisão técnica (`MANUAL_REVIEW_REQUIRED`)          |
| **RULE-BNDES-006** | Idoneidade e Transparência (CEIS / CNEP)    | Lei no 12.846/2013 (Anticorrupção); Diretrizes de Compliance | Determinística          | Ausência de inscrição nos cadastros de empresas inidoneas e suspensas                 | Bloqueio imediato (`NON_COMPLIANT`)                             |

---

## 3. Política de Tolerância Zero e Classificação de Risco

1. **Infrações Criticas**: Débitos tributários com a Fazenda Nacional ou inscrição ativa no CEIS/CNEP resultam em reprovação sumaria do dossie sem possibilidade de sobrestamento pelo motor de regras.
2. **Casos Ambiguos e Baixa Qualidade de Imagem**: Documentos com carimbos ilegíveis ou corte de margem acionam o protocolo de degradação para revisão manual, impedindo a aprovação indevida por omissão de dados.
3. **Imutabilidade do Laudo**: Todo parecer gerado pelo motor de regras e gravado com chave estrangeira para o documento original, registrando o estado das regras no instante da verificação.

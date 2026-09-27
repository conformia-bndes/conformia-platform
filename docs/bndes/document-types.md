# Tipologias de Documentos e Especificacoes de Ingestao

Este documento estabelece as especificacoes tecnicas das tipologias documentais processadas pelo pipeline de IDP do Conform.IA BNDES, detalhando orgaos emissores, campos obrigatorios, expressoes regulares e condicoes de contorno.

---

## 1. Certidao Negativa de Debitos Federais (CND Federal)

- **Orgao Emissor**: Secretaria Especial da Receita Federal do Brasil (RFB) e Procuradoria-Geral da Fazenda Nacional (PGFN).
- **Finalidade**: Comprovar a quitacao de tributos federais e contribuicoes previdenciarias inscritas em Divida Ativa da Uniao.
- **Campos Obrigatorios**:
  - CNPJ da empresa proponente (formato: `XX.XXX.XXX/XXXX-XX`).
  - Razao Social da pessoa juridica.
  - Codigo de controle da certidao.
  - Data de emissao e data limite de validade.
  - Frase de efeito legal: *"certidao negativa de debitos relativos aos tributos federais e a divida ativa da uniao"* ou *"certidao positiva com efeitos de negativa"*.
- **Expressoes Regulares**:
  - CNPJ: `\b[0-9]{2}\.[0-9]{3}\.[0-9]{3}\/[0-9]{4}\-[0-9]{2}\b`
  - Codigo de Controle: `[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4}`

---

## 2. Certificado de Regularidade do FGTS (CRF)

- **Orgao Emissor**: Caixa Economica Federal (CEF).
- **Finalidade**: Atestar o cumprimento das obrigacoes trabalhistas com o Fundo de Garantia do Tempo de Servico.
- **Campos Obrigatorios**:
  - Razao Social e Endereco do empregador.
  - Inscricao CNPJ ou CEI.
  - Numero do Certificado (CRF).
  - Periodo de validade (de DD/MM/AAAA a DD/MM/AAAA).
  - Atestado de situacao regular: *"encontra-se em situacao regular perante o Fundo de Garantia do Tempo de Servico"*.

---

## 3. Certidao Negativa de Debitos Trabalhistas (CNDT)

- **Orgao Emissor**: Justica do Trabalho / Tribunal Superior do Trabalho (TST).
- **Finalidade**: Demonstrar que o proponente nao figura como inadimplente no Banco Nacional de Devedores Trabalhistas (BNDT).
- **Campos Obrigatorios**:
  - Nome / Razao Social.
  - CNPJ.
  - Numero da certidao e ano de expedicao.
  - Declaracao formal de que *"NAO CONSTAM"* debitos trabalhistas inadimplidos.

---

## 4. Certidao dos Distribuidores Civeis (Falencia e Recuperacao)

- **Orgao Emissor**: Tribunais de Justica Estaduais (Varas de Falencia e Recuperacoes Judiciais da Comarca da sede da empresa).
- **Finalidade**: Certificar a inexistencia de pedidos de falencia decretada ou plano de recuperacao judicial nao homologado.
- **Tratamento Hibrido (Maker-Checker)**:
  - Textos de certidoes judiciais variam conforme a comarca estadual.
  - O pipeline IDP extrai o texto integral; o agente Maker avalia a presenca de acoes distribuidas; o agente Checker confirma se nao ha mencao a decretacao falimentar.

---

## 5. Licenciamento Ambiental e Atos Autorizativos

- **Orgao Emissor**: IBAMA ou orgaos estaduais competentes (ex: INEA/RJ, CETESB/SP, FEPAM/RS).
- **Tipos de Licenca Aceitas**:
  - Licenca Previa (LP)
  - Licenca de Instalacao (LI)
  - Licenca de Operacao (LO)
  - Certidao de Inexigibilidade ou Dispensa de Licenciamento
- **Campos Obrigatorios**:
  - Identificacao do empreendimento e coordenadas geograficas.
  - Tipologia da atividade e numero do processo administrativo.
  - Condicionantes e prazo de vigencia da licenca.

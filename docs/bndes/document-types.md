# Tipologias de Documentos e Especificações de Ingestão

Este documento estabelece as especificações técnicas das tipologias documentais processadas pelo pipeline de IDP do Conform.IA BNDES, detalhando órgãos emissores, campos obrigatórios, expressões regulares e condições de contorno.

---

## 1. Certidão Negativa de Débitos Federais (CND Federal)

- **Órgão Emissor**: Secretaria Especial da Receita Federal do Brasil (RFB) e Procuradoria-Geral da Fazenda Nacional (PGFN).
- **Finalidade**: Comprovar a quitação de tributos federais e contribuições previdenciárias inscritas em Dívida Ativa da União.
- **Campos Obrigatórios**:
  - CNPJ da empresa proponente (formato: `XX.XXX.XXX/XXXX-XX`).
  - Razão Social da pessoa jurídica.
  - Código de controle da certidão.
  - Data de emissão e data limite de validade.
  - Frase de efeito legal: _"certidao negativa de debitos relativos aos tributos federais e a divida ativa da uniao"_ ou _"certidao positiva com efeitos de negativa"_.
- **Expressoes Regulares**:
  - CNPJ: `\b[0-9]{2}\.[0-9]{3}\.[0-9]{3}\/[0-9]{4}\-[0-9]{2}\b`
  - Codigo de Controle: `[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4}`

---

## 2. Certificado de Regularidade do FGTS (CRF)

- **Órgão Emissor**: Caixa Econômica Federal (CEF).
- **Finalidade**: Atestar o cumprimento das obrigações trabalhistas com o Fundo de Garantia do Tempo de Serviço.
- **Campos Obrigatórios**:
  - Razao Social e Endereco do empregador.
  - Inscricao CNPJ ou CEI.
  - Numero do Certificado (CRF).
  - Periodo de validade (de DD/MM/AAAA a DD/MM/AAAA).
  - Atestado de situacao regular: _"encontra-se em situacao regular perante o Fundo de Garantia do Tempo de Servico"_.

---

## 3. Certidão Negativa de Débitos Trabalhistas (CNDT)

- **Órgão Emissor**: Justiça do Trabalho / Tribunal Superior do Trabalho (TST).
- **Finalidade**: Demonstrar que o proponente não figura como inadimplente no Banco Nacional de Devedores Trabalhistas (BNDT).
- **Campos Obrigatórios**:
  - Nome / Razao Social.
  - CNPJ.
  - Numero da certidao e ano de expedicao.
  - Declaracao formal de que _"NAO CONSTAM"_ debitos trabalhistas inadimplidos.

---

## 4. Certidão dos Distribuidores Cíveis (Falência e Recuperação)

- **Órgão Emissor**: Tribunais de Justiça Estaduais (Varas de Falência e Recuperações Judiciais da comarca da sede da empresa).
- **Finalidade**: Certificar a inexistência de pedidos de falência decretada ou plano de recuperação judicial não homologado.
- **Tratamento Hibrido (Maker-Checker)**:
  - Textos de certidoes judiciais variam conforme a comarca estadual.
  - O pipeline IDP extrai o texto integral; o agente Maker avalia a presenca de acoes distribuidas; o agente Checker confirma se nao ha mencao a decretacao falimentar.

---

## 5. Licenciamento Ambiental e Atos Autorizativos

- **Órgão Emissor**: IBAMA ou órgãos estaduais competentes (ex.: INEA/RJ, CETESB/SP, FEPAM/RS).
- **Tipos de Licença Aceitos**:
  - Licença Prévia (LP)
  - Licença de Instalação (LI)
  - Licença de Operação (LO)
  - Certidão de Inexigibilidade ou Dispensa de Licenciamento
- **Campos Obrigatórios**:
  - Identificação do empreendimento e coordenadas geográficas.
  - Tipologia da atividade e número do processo administrativo.
  - Condicionantes e prazo de vigência da licença.

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
  - Frase de efeito legal: _"certidão negativa de débitos relativos aos tributos federais e a dívida ativa da União"_ ou _"certidão positiva com efeitos de negativa"_.
- **Expressões Regulares**:
  - CNPJ: `\b[0-9]{2}\.[0-9]{3}\.[0-9]{3}\/[0-9]{4}\-[0-9]{2}\b`
  - Código de Controle: `[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4}`

---

## 2. Certificado de Regularidade do FGTS (CRF)

- **Órgão Emissor**: Caixa Econômica Federal (CEF).
- **Finalidade**: Atestar o cumprimento das obrigações trabalhistas com o Fundo de Garantia do Tempo de Serviço.
- **Campos Obrigatórios**:
  - Razão Social e Endereço do empregador.
  - Inscrição CNPJ ou CEI.
  - Número do Certificado (CRF).
  - Período de validade (de DD/MM/AAAA a DD/MM/AAAA).
  - Atestado de situação regular: _"encontra-se em situação regular perante o Fundo de Garantia do Tempo de Serviço"_.

---

## 3. Certidão Negativa de Débitos Trabalhistas (CNDT)

- **Órgão Emissor**: Justiça do Trabalho / Tribunal Superior do Trabalho (TST).
- **Finalidade**: Demonstrar que o proponente não figura como inadimplente no Banco Nacional de Devedores Trabalhistas (BNDT).
- **Campos Obrigatórios**:
  - Nome / Razão Social.
  - CNPJ.
  - Número da certidão e ano de expedição.
  - Declaração formal de que _"NÃO CONSTAM"_ débitos trabalhistas inadimplidos.

---

## 4. Certidão dos Distribuidores Cíveis (Falência e Recuperação)

- **Órgão Emissor**: Tribunais de Justiça Estaduais (Varas de Falência e Recuperações Judiciais da comarca da sede da empresa).
- **Finalidade**: Certificar a inexistência de pedidos de falência decretada ou plano de recuperação judicial não homologado.
- **Tratamento Híbrido (Maker-Checker)**:
  - Textos de certidões judiciais variam conforme a comarca estadual.
  - O pipeline IDP extrai o texto integral; o agente Maker avalia a presença de ações distribuidas; o agente Checker confirma se não há menção a decretação falimentar.

---

## 5. Licenciamento Ambiental e Atos Autorizativos

- **Órgão Emissor**: IBAMA ou órgãos estaduais competentes (ex.: INEA/RJ, CETESB/SP, FEPAM/RS).
- **Tipos de Licença Aceitos**:
  - Licença Prévia (LP)
  - Licença de Instalação (LI)
  - Licença de Operação (LO)
  - Certidão de Inexigibilidade ou Dispensa de Licenciamento
- **Detecção no parser**: exige a expressão "licença ambiental" ou "licença prévia / de
  instalação / de operação" **e** um órgão ambiental no texto (IBAMA, "órgão ambiental",
  "meio ambiente", INEA, CETESB ou FEPAM). Licenças de outros órgãos, ou sem órgão no texto,
  ficam sem tipologia e vão para revisão manual. A evidência é a linha da expressão.
- **Limitação atual**: a Certidão de Inexigibilidade ou Dispensa de Licenciamento é aceita
  pela política, mas **não é detectada pelo parser**: fica sem tipologia e vai para revisão manual.
- **Campos Obrigatórios**:
  - Identificação do empreendimento e coordenadas geográficas.
  - Tipologia da atividade e número do processo administrativo.
  - Condicionantes e prazo de vigência da licença.

---

## 6. Consulta de Integridade (CEIS / CNEP)

- **Órgão Emissor**: Controladoria-Geral da União (CGU), via Portal da Transparência.
- **Finalidade**: Verificar se o proponente tem sanção vigente no Cadastro Nacional de Empresas
  Inidôneas e Suspensas (CEIS) ou no Cadastro Nacional de Empresas Punidas (CNEP, Lei nº 12.846/2013).
- **Detecção no parser**: siglas `CEIS` ou `CNEP` (palavra inteira) ou o nome por extenso de um
  dos cadastros, sem depender de acentos. É testada antes da licença ambiental, porque a
  consulta pode citar o IBAMA. Menções soltas a falência, recuperação judicial ou CNDT não
  mudam a tipologia; só uma certidão com o sinal da própria tipologia ("débitos trabalhistas";
  distribuidor + falência/recuperação judicial) tem precedência sobre a consulta.
- **Tratamento Híbrido (Maker-Checker)**:
  - Os termos de sanção definidos na regra (`anti_keywords`; ex.: "impedimento de licitar")
    reprovam direto (`NON_COMPLIANT`).
  - Um "nada consta" pode se referir a só um dos cadastros; sem LLM, a consulta vai para
    revisão manual e nunca é aprovada automaticamente.
- **Campos Esperados**: CNPJ consultado, resultado por cadastro e data da consulta.

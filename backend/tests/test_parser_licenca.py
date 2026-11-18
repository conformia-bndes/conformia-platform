"""Testes da deteccao da tipologia LICENCA_AMBIENTAL (RULE-BNDES-005) no parser IDP."""

import unicodedata

import pytest

from app.idp.parser import extract_fields_and_evidence


def test_detecta_licenca_ambiental_com_evidencia_na_pagina():
    page_1 = "GOVERNO DO ESTADO\nORGAO AMBIENTAL ESTADUAL\n"
    page_2 = (
        "LICENÇA AMBIENTAL DE OPERAÇÃO N. 0456/2025\n"
        "CNPJ: 12.345.678/0001-90\n"
        "Válida até: 30/06/2028\n"
    )
    pages = [{"page_number": 1, "text": page_1}, {"page_number": 2, "text": page_2}]

    result = extract_fields_and_evidence(f"{page_1}\n{page_2}", pages=pages)

    assert result.document_type == "LICENCA_AMBIENTAL"
    field = result.fields["document_type"]
    assert field.value == "LICENCA_AMBIENTAL"
    assert field.evidence.page == 2
    assert "LICENÇA AMBIENTAL DE OPERAÇÃO" in field.evidence.text


def test_detecta_licenca_de_operacao_do_ibama_sem_a_palavra_ambiental():
    text = "IBAMA\nLICENCA DE OPERACAO N. 1010/2026\nValida ate: 01/03/2029"
    assert extract_fields_and_evidence(text).document_type == "LICENCA_AMBIENTAL"


def test_licenca_nao_ambiental_nao_e_detectada():
    text = "PREFEITURA MUNICIPAL\nLICENCA SANITARIA MUNICIPAL\nValida ate: 01/03/2027"
    assert extract_fields_and_evidence(text).document_type is None


def test_recuperacao_de_area_degradada_nao_vira_falencia():
    text = (
        "ORGAO AMBIENTAL ESTADUAL\n"
        "LICENCA AMBIENTAL DE INSTALACAO N. 0789/2026\n"
        "Condicionante: PLANO DE RECUPERACAO DE AREA DEGRADADA (PRAD)\n"
        "Valida ate: 30/06/2028"
    )
    assert extract_fields_and_evidence(text).document_type == "LICENCA_AMBIENTAL"


@pytest.mark.parametrize(
    "text, expected_type",
    [
        (
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
            "E A DIVIDA ATIVA DA UNIAO\n"
            "Finalidade: instruir pedido de licenca ambiental",
            "CND_FEDERAL",
        ),
        (
            "CAIXA ECONOMICA FEDERAL\nCERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
            "Finalidade: licenca ambiental de operacao",
            "CRF_FGTS",
        ),
        (
            "PODER JUDICIARIO - JUSTICA DO TRABALHO\n"
            "CERTIDAO NEGATIVA DE DEBITOS TRABALHISTAS\nFinalidade: licenca ambiental",
            "CNDT_TRABALHISTA",
        ),
        (
            "CERTIDAO DOS DISTRIBUIDORES CIVEIS\n"
            "NADA CONSTA DE FALENCIA E RECUPERACAO JUDICIAL\n"
            "Finalidade: renovacao de licenca ambiental",
            "FALENCIA_RECUPERACAO",
        ),
    ],
)
def test_tipologias_existentes_nao_viram_licenca(text, expected_type):
    assert extract_fields_and_evidence(text).document_type == expected_type


@pytest.mark.parametrize(
    "text",
    [
        "VIGILANCIA SANITARIA MUNICIPAL\nLICENCA SANITARIA N. 55/2026\n"
        "Responsavel tecnico ambiental: Joao",
        "CONTRATO DE LICENCA DE USO DE SOFTWARE\nModulo de gestao ambiental",
        "REQUERIMENTO DE LICENCA-MATERNIDADE\nSecretaria de Meio Ambiente - RH",
        "IBAMA\nLICENCA DE PESCA AMADORA\nValida ate: 01/01/2027",
        "ANATEL - AGENCIA NACIONAL DE TELECOMUNICACOES\nLICENCA DE OPERACAO DE ESTACAO",
        "ANAC\nLICENCA DE OPERACAO DE AERODROMO\nValida ate: 01/01/2027",
        "LICENCA AMBIENTAL\nValida ate: 01/01/2027",
    ],
    ids=["sanitaria", "software", "maternidade", "pesca-ibama", "anatel", "anac", "sem-orgao"],
)
def test_licencas_nao_ambientais_nao_sao_detectadas(text):
    result = extract_fields_and_evidence(text)
    assert result.document_type is None
    assert "document_type" not in result.fields


@pytest.mark.parametrize(
    "text, expected_snippet",
    [
        (
            "CETESB - COMPANHIA AMBIENTAL DO ESTADO DE SAO PAULO\n"
            "LICENCA DE OPERACAO N. 12\nValida ate: 01/01/2028",
            "LICENCA DE OPERACAO N. 12",
        ),
        ("SECRETARIA MUNICIPAL DE MEIO AMBIENTE\nLICENCA PREVIA N. 9", "LICENCA PREVIA N. 9"),
    ],
)
def test_licenca_detectada_com_orgao_estadual_ou_secretaria(text, expected_snippet):
    result = extract_fields_and_evidence(text)
    assert result.document_type == "LICENCA_AMBIENTAL"
    assert result.fields["document_type"].evidence.text == expected_snippet


def test_licenca_que_cita_falencia_nas_condicionantes_continua_licenca():
    text = (
        "ORGAO AMBIENTAL ESTADUAL\n"
        "LICENCA AMBIENTAL DE OPERACAO N. 77\n"
        "Condicionante: em caso de falencia do titular, a licenca perde efeito\n"
        "Valida ate: 01/01/2028"
    )
    result = extract_fields_and_evidence(text)
    assert result.document_type == "LICENCA_AMBIENTAL"
    assert result.fields["document_type"].evidence.text == "LICENCA AMBIENTAL DE OPERACAO N. 77"


def test_evidencia_da_licenca_usa_o_padrao_da_deteccao():
    # A pagina 1 cita "licenca" solta; a evidencia precisa apontar a licenca da pagina 2.
    page_1 = "INEA - INSTITUTO ESTADUAL DO AMBIENTE\nRequerimento de licenca protocolado em 2025"
    page_2 = "LICENÇA AMBIENTAL DE INSTALAÇÃO N. 31/2026\nVálida até: 01/01/2029"
    pages = [{"page_number": 1, "text": page_1}, {"page_number": 2, "text": page_2}]

    result = extract_fields_and_evidence(f"{page_1}\n{page_2}", pages=pages)

    assert result.document_type == "LICENCA_AMBIENTAL"
    evidence = result.fields["document_type"].evidence
    assert evidence.page == 2
    assert evidence.text == "LICENÇA AMBIENTAL DE INSTALAÇÃO N. 31/2026"


def test_licenca_em_nfd_tem_tipo_e_evidencia():
    text = unicodedata.normalize(
        "NFD",
        "ÓRGÃO AMBIENTAL ESTADUAL\nLICENÇA AMBIENTAL DE OPERAÇÃO N. 5\nVálida até: 01/01/2028",
    )
    result = extract_fields_and_evidence(text)
    assert result.document_type == "LICENCA_AMBIENTAL"
    assert result.fields["document_type"].evidence.text == "LICENÇA AMBIENTAL DE OPERAÇÃO N. 5"

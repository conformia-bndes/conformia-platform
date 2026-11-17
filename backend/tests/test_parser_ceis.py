"""Testes da deteccao da tipologia INTEGRIDADE_CEIS_CNEP (RULE-BNDES-006) no parser IDP."""

import pytest

from app.idp.parser import extract_fields_and_evidence


def test_detecta_ceis_com_evidencia_na_pagina():
    page_1 = "PORTAL DA TRANSPARENCIA\nCONTROLADORIA-GERAL DA UNIAO\n"
    page_2 = (
        "CADASTRO NACIONAL DE EMPRESAS INIDÔNEAS E SUSPENSAS (CEIS)\n"
        "CNPJ: 12.345.678/0001-90\n"
        "Resultado: NADA CONSTA\n"
    )
    pages = [{"page_number": 1, "text": page_1}, {"page_number": 2, "text": page_2}]

    result = extract_fields_and_evidence(f"{page_1}\n{page_2}", pages=pages)

    assert result.document_type == "INTEGRIDADE_CEIS_CNEP"
    field = result.fields["document_type"]
    assert field.value == "INTEGRIDADE_CEIS_CNEP"
    assert field.evidence.page == 2
    assert "(CEIS)" in field.evidence.text


def test_detecta_cnep_so_pela_sigla():
    assert extract_fields_and_evidence("CONSULTA CNEP").document_type == "INTEGRIDADE_CEIS_CNEP"


def test_consulta_ceis_que_cita_licenca_e_ibama_continua_ceis():
    text = (
        "CADASTRO NACIONAL DE EMPRESAS INIDONEAS E SUSPENSAS (CEIS)\n"
        "Orgao sancionador: IBAMA - Licenca ambiental de operacao cassada\n"
        "Sancao: IMPEDIMENTO DE LICITAR E CONTRATAR"
    )
    assert extract_fields_and_evidence(text).document_type == "INTEGRIDADE_CEIS_CNEP"


def test_licenca_que_nao_cita_ceis_continua_licenca():
    text = (
        "IBAMA - ORGAO AMBIENTAL FEDERAL\n"
        "LICENCA AMBIENTAL DE OPERACAO N. 1010/2026\n"
        "Valida ate: 01/03/2029"
    )
    assert extract_fields_and_evidence(text).document_type == "LICENCA_AMBIENTAL"


@pytest.mark.parametrize(
    "text, expected_type",
    [
        (
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
            "E A DIVIDA ATIVA DA UNIAO\n"
            "Documento apresentado junto com a consulta CEIS",
            "CND_FEDERAL",
        ),
        (
            "CAIXA ECONOMICA FEDERAL\nCERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
            "Documento apresentado junto com a consulta CEIS",
            "CRF_FGTS",
        ),
        (
            "PODER JUDICIARIO - JUSTICA DO TRABALHO\n"
            "CERTIDAO NEGATIVA DE DEBITOS TRABALHISTAS\n"
            "Documento apresentado junto com a consulta CEIS",
            "CNDT_TRABALHISTA",
        ),
        (
            "CERTIDAO DOS DISTRIBUIDORES CIVEIS\n"
            "NADA CONSTA DE FALENCIA E RECUPERACAO JUDICIAL\n"
            "Documento apresentado junto com a consulta CEIS",
            "FALENCIA_RECUPERACAO",
        ),
    ],
)
def test_tipologias_existentes_nao_viram_ceis(text, expected_type):
    assert extract_fields_and_evidence(text).document_type == expected_type

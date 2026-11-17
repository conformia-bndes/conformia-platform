"""Testes da deteccao da tipologia LICENCA_AMBIENTAL (RULE-BNDES-005) no parser IDP."""

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

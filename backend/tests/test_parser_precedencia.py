"""Precedencia entre tipologias e normalizacao de acentos no parser IDP."""

import unicodedata

import pytest

from app.idp.parser import extract_fields_and_evidence


@pytest.mark.parametrize(
    "text, expected_type",
    [
        # Sinal fraco sem CEIS/licenca: continua como hoje.
        ("CERTIDAO DE FALENCIA\nNADA CONSTA", "FALENCIA_RECUPERACAO"),
        ("CNDT N. 123/2026\nNao constam debitos", "CNDT_TRABALHISTA"),
        # Sinal forte da propria certidao vence a mencao ao CEIS.
        (
            "CERTIDAO DOS DISTRIBUIDORES CIVEIS\n"
            "NADA CONSTA DE FALENCIA E RECUPERACAO JUDICIAL\n"
            "Documento apresentado junto com a consulta CEIS",
            "FALENCIA_RECUPERACAO",
        ),
        (
            "JUSTICA DO TRABALHO\nCERTIDAO NEGATIVA DE DEBITOS TRABALHISTAS\n"
            "Documento apresentado junto com a consulta CEIS",
            "CNDT_TRABALHISTA",
        ),
    ],
    ids=["falencia-fraca", "cndt-sigla", "falencia-distribuidor-cita-ceis", "cndt-forte-cita-ceis"],
)
def test_falencia_e_cndt_mantem_tipologia(text, expected_type):
    result = extract_fields_and_evidence(text)
    assert result.document_type == expected_type
    assert result.fields["document_type"].value == expected_type


def test_cnd_em_nfd_tem_tipo_e_evidencia():
    text = unicodedata.normalize(
        "NFD",
        "RECEITA FEDERAL\nCERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
        "Válida até: 31/12/2026",
    )
    result = extract_fields_and_evidence(text)
    assert result.document_type == "CND_FEDERAL"
    assert (
        result.fields["document_type"].evidence.text
        == "CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS"
    )


def test_normalizacao_nao_altera_as_paginas_de_quem_chama():
    original = unicodedata.normalize("NFD", "CONSULTA CEIS\nNADA CONSTA")
    pages = [{"page_number": 1, "text": original}]

    extract_fields_and_evidence(original, pages=pages)

    assert pages[0]["text"] == original

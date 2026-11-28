"""Advanced unit tests for rules engine: regex validation and temporal validity."""

from datetime import date

import pytest

from app.idp.parser import extract_fields_and_evidence, scan_validity_dates
from app.services.rules_engine import RulesEngine, summarize_statuses


def test_rules_engine_expired_certificate():
    """Certidao com data de validade expirada deve ser NON_COMPLIANT."""
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 01/01/2020"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data)
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "NON_COMPLIANT"
    assert "expirada" in cnd_check["findings"].lower()


def test_rules_engine_valid_future_certificate():
    """Certidao com data futura valida deve ser COMPLIANT."""
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 31/12/2030"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data)
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "COMPLIANT"


def test_rules_engine_category_filtering():
    """Ao filtrar por categoria FISCAL, regras TRABALHISTA devem ser NOT_APPLICABLE."""
    engine = RulesEngine()
    mock_data = {
        "full_text": (
            "REPUBLICA FEDERATIVA DO BRASIL - MINISTERIO DA FAZENDA\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Valida ate: 31/12/2099"
        ),
        "metadata": {},
    }
    result = engine.evaluate(mock_data, target_category="FISCAL")
    fiscal_check = next(r for r in result["results"] if r["category"] == "FISCAL")
    other_checks = [r for r in result["results"] if r["category"] != "FISCAL"]

    assert fiscal_check["status"] == "COMPLIANT"
    assert all(r["status"] == "NOT_APPLICABLE" for r in other_checks)


CND_TEXT = (
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
    "E A DIVIDA ATIVA DA UNIAO\n"
    "CNPJ: 12.345.678/0001-90\n"
)
FIXED_TODAY = date(2026, 10, 29)


def _cnd_status(text: str) -> str:
    engine = RulesEngine(today=lambda: FIXED_TODAY)
    result = engine.evaluate({"full_text": text}, document_type="CND_FEDERAL")
    return next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")["status"]


def test_missing_validity_date_requires_manual_review():
    """AGENTS.md diretriz 1: sem data de validade legivel, nunca COMPLIANT."""
    assert _cnd_status(CND_TEXT) == "MANUAL_REVIEW_REQUIRED"


def test_validity_on_reference_day_is_still_valid():
    """A certidao vale ate o fim do dia de validade."""
    assert _cnd_status(CND_TEXT + "Valida ate: 29/10/2026") == "COMPLIANT"


def test_validity_one_day_before_reference_is_expired():
    assert _cnd_status(CND_TEXT + "Valida ate: 28/10/2026") == "NON_COMPLIANT"


def test_unparseable_validity_date_requires_manual_review():
    """Data impossivel (31/02) nao e tratada como validade."""
    assert _cnd_status(CND_TEXT + "Valida ate: 31/02/2027") == "MANUAL_REVIEW_REQUIRED"


def test_document_type_scopes_rules_to_matching_code():
    """Uma CND valida nao pode ser reprovada pelas regras de CRF, CNDT, falencia etc."""
    engine = RulesEngine(today=lambda: FIXED_TODAY)
    result = engine.evaluate(
        {"full_text": CND_TEXT + "Valida ate: 31/12/2026"}, document_type="CND_FEDERAL"
    )
    by_rule = {r["rule_id"]: r["status"] for r in result["results"]}

    assert by_rule["RULE-BNDES-001"] == "COMPLIANT"
    assert all(
        status == "NOT_APPLICABLE" for rid, status in by_rule.items() if rid != "RULE-BNDES-001"
    )
    assert result["overall_status"] == "COMPLIANT"
    assert result["evaluated_rules"] == 1
    assert result["compliance_score"] == 1.0


def test_document_type_without_matching_rule_is_manual_review():
    engine = RulesEngine(today=lambda: FIXED_TODAY)
    result = engine.evaluate({"full_text": CND_TEXT}, document_type="TIPO_SEM_REGRA")
    assert result["evaluated_rules"] == 0
    assert result["overall_status"] == "MANUAL_REVIEW_REQUIRED"


def test_not_evaluable_is_manual_review_and_applies_no_rule():
    engine = RulesEngine()
    result = engine.not_evaluable("Tipologia nao identificada.")
    assert result["overall_status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["compliance_score"] == 0.0
    assert all(r["status"] == "NOT_APPLICABLE" for r in result["results"])


def test_summarize_statuses_ignores_not_applicable():
    assert summarize_statuses(["COMPLIANT", "NOT_APPLICABLE"]) == ("COMPLIANT", 1.0)
    assert summarize_statuses(["COMPLIANT", "MANUAL_REVIEW_REQUIRED"]) == (
        "MANUAL_REVIEW_REQUIRED",
        0.5,
    )
    assert summarize_statuses(["COMPLIANT", "NON_COMPLIANT", "MANUAL_REVIEW_REQUIRED"])[0] == (
        "NON_COMPLIANT"
    )
    assert summarize_statuses(["NOT_APPLICABLE"]) == ("MANUAL_REVIEW_REQUIRED", 0.0)
    assert summarize_statuses([]) == ("MANUAL_REVIEW_REQUIRED", 0.0)


def test_missing_required_keyword_goes_to_manual_review():
    """Decisao D2: termo obrigatorio ausente (ex.: OCR ilegivel) nao reprova, vai ao analista."""
    engine = RulesEngine()
    text = (
        "MINISTERIO DA FAZENDA\nCERTIDAO NEGATIVA\n"
        "CARIMBO SOBREPOSTO ILEGIVEL\nValida ate: 31/12/2099"
    )
    result = engine.evaluate({"full_text": text}, document_type="CND_FEDERAL")
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "MANUAL_REVIEW_REQUIRED"
    assert cnd_check["evidence"]["missing_keywords"]
    assert result["overall_status"] == "MANUAL_REVIEW_REQUIRED"


def test_anti_keyword_still_non_compliant_even_when_text_is_incomplete():
    """Termo impeditivo continua reprovando, independentemente da decisao D2."""
    engine = RulesEngine()
    text = "CERTIDAO POSITIVA\nCONSTA PENDENCIA\nValida ate: 31/12/2099"
    result = engine.evaluate({"full_text": text}, document_type="CND_FEDERAL")
    cnd_check = next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-001")
    assert cnd_check["status"] == "NON_COMPLIANT"


class _FakeMakerChecker:
    """Maker-Checker de teste: registra as chamadas e devolve um veredito fixo."""

    def __init__(self, status="MANUAL_REVIEW_REQUIRED"):
        self.status = status
        self.calls = 0

    def evaluate_rule(self, rule, full_text):
        self.calls += 1
        return {"status": self.status, "final_confidence": 0.5, "reasoning": "teste"}


_CEIS = "CADASTRO NACIONAL DE EMPRESAS INIDONEAS E SUSPENSAS (CEIS)"
_CNEP = "CADASTRO NACIONAL DE EMPRESAS PUNIDAS (CNEP)"


def _rule_006(text, maker_checker):
    engine = RulesEngine(maker_checker=maker_checker)
    result = engine.evaluate({"full_text": text, "metadata": {}})
    return next(r for r in result["results"] if r["rule_id"] == "RULE-BNDES-006")


def test_rule_006_does_not_auto_approve_ceis_nada_consta():
    """CEIS + 'nada consta' nao aprova sozinho: falta o CNEP e vai a revisao."""
    checker = _FakeMakerChecker()
    res = _rule_006(f"{_CEIS}\nNADA CONSTA", checker)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"
    assert checker.calls == 0


def test_rule_006_cnep_sanction_is_non_compliant():
    """Sancao do CNEP (multa) com 'nada consta' do CEIS reprova."""
    checker = _FakeMakerChecker()
    text = f"{_CEIS}\nNADA CONSTA\n{_CNEP}\nMULTA APLICADA: R$ 50.000,00"
    assert _rule_006(text, checker)["status"] == "NON_COMPLIANT"


def test_rule_006_both_registries_goes_through_maker_checker():
    """Com os dois cadastros citados, a decisao passa pelo Maker-Checker."""
    checker = _FakeMakerChecker(status="COMPLIANT")
    res = _rule_006(f"{_CEIS}\nNADA CONSTA\n{_CNEP}\nNADA CONSTA", checker)
    assert checker.calls == 1
    assert res["checker_type"] == "MAKER_CHECKER"


# ==============================================================================
# Issue #162: validade multipla, termos impeditivos ampliados e regex_patterns
# ==============================================================================

CERT_TEMPLATES = [
    pytest.param(
        "CND_FEDERAL",
        "RULE-BNDES-001",
        (
            "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
            "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
            "E A DIVIDA ATIVA DA UNIAO\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Nao constam pendencias.\n"
        ),
        id="cnd",
    ),
    pytest.param(
        "CRF_FGTS",
        "RULE-BNDES-002",
        (
            "CAIXA ECONOMICA FEDERAL\n"
            "CERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Certificado: CRF202612050001\n"
            "SITUACAO REGULAR perante o FGTS.\n"
        ),
        id="crf",
    ),
    pytest.param(
        "CNDT_TRABALHISTA",
        "RULE-BNDES-003",
        (
            "PODER JUDICIARIO - JUSTICA DO TRABALHO\n"
            "CERTIDAO NEGATIVA DE DEBITOS TRABALHISTAS\n"
            "CNPJ: 12.345.678/0001-90\n"
            "Nao constam debitos inadimplidos.\n"
        ),
        id="cndt",
    ),
]


def _eval_rule(doc_type: str, rule_id: str, text: str, ref_date: date = date(2026, 12, 5)):
    engine = RulesEngine(today=lambda: ref_date)
    result = engine.evaluate({"full_text": text}, document_type=doc_type)
    return next(r for r in result["results"] if r["rule_id"] == rule_id)


def test_issue_162_reproduction_scenarios_never_return_compliant():
    """Os 3 cenarios exatos descritos na issue #162 deixam de resultar em COMPLIANT."""
    header = (
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
        "E A DIVIDA ATIVA DA UNIAO\n"
    )
    ref = date(2026, 12, 5)

    # Cenario 1: validade futura seguida de validade vencida (e ordem inversa)
    s1 = _eval_rule(
        "CND_FEDERAL",
        "RULE-BNDES-001",
        header + "CNPJ: 12.345.678/0001-90\nValidade 30/06/2030. Valida ate 01/01/2020",
        ref_date=ref,
    )
    assert s1["status"] == "NON_COMPLIANT"

    # Cenario 2: redacao impeditiva "Constam debitos em cobranca administrativa"
    s2 = _eval_rule(
        "CND_FEDERAL",
        "RULE-BNDES-001",
        header
        + "CNPJ: 12.345.678/0001-90\n"
        + "Constam debitos em cobranca administrativa. Valida ate 30/06/2027",
        ref_date=ref,
    )
    assert s2["status"] == "NON_COMPLIANT"

    # Cenario 3: cabecalho sem CNPJ + validade futura
    s3 = _eval_rule(
        "CND_FEDERAL",
        "RULE-BNDES-001",
        header + "Valida ate 30/06/2027",
        ref_date=ref,
    )
    assert s3["status"] == "MANUAL_REVIEW_REQUIRED"
    assert s3["evidence"]["missing_regex_patterns"]


@pytest.mark.parametrize("doc_type, rule_id, base_text", CERT_TEMPLATES)
def test_validity_decision_matrix_for_cnd_crf_cndt(doc_type, rule_id, base_text):
    """Matriz completa de validade aplicada a CND, CRF e CNDT."""
    # Uma data valida vigente -> COMPLIANT
    assert _eval_rule(doc_type, rule_id, base_text + "Valida ate: 30/06/2027")["status"] == (
        "COMPLIANT"
    )

    # Mesma data vigente repetida em cabecalho/rodape -> COMPLIANT
    repeated = base_text + "Valida ate: 30/06/2027\nPagina 2 - Validade: 30/06/2027"
    assert _eval_rule(doc_type, rule_id, repeated)["status"] == "COMPLIANT"

    # Uma data vencida -> NON_COMPLIANT
    assert _eval_rule(doc_type, rule_id, base_text + "Valida ate: 01/01/2020")["status"] == (
        "NON_COMPLIANT"
    )

    # Duas datas (futura + vencida) nas duas ordens -> NON_COMPLIANT em ambas
    future_first = base_text + "Validade 30/06/2030. Valida ate 01/01/2020"
    expired_first = base_text + "Valida ate 01/01/2020. Validade 30/06/2030"
    assert _eval_rule(doc_type, rule_id, future_first)["status"] == "NON_COMPLIANT"
    assert _eval_rule(doc_type, rule_id, expired_first)["status"] == "NON_COMPLIANT"

    # Duas datas vigentes diferentes entre si -> MANUAL_REVIEW_REQUIRED
    two_future = base_text + "Validade: 30/06/2027. Vigencia: 31/12/2027"
    assert _eval_rule(doc_type, rule_id, two_future)["status"] == "MANUAL_REVIEW_REQUIRED"

    # Somente data impossivel -> MANUAL_REVIEW_REQUIRED
    impossible = base_text + "Valida ate: 31/02/2026"
    res_imp = _eval_rule(doc_type, rule_id, impossible)
    assert res_imp["status"] == "MANUAL_REVIEW_REQUIRED"
    assert "31/02/2026" in res_imp["evidence"]["invalid_validity_dates"]

    # Data impossivel + data vigente -> MANUAL_REVIEW_REQUIRED
    mixed_imp = base_text + "Valida ate: 31/02/2026. Validade: 30/06/2027"
    assert _eval_rule(doc_type, rule_id, mixed_imp)["status"] == "MANUAL_REVIEW_REQUIRED"

    # Data impossivel + data vencida -> NON_COMPLIANT
    expired_imp = base_text + "Valida ate: 31/02/2026. Validade: 01/01/2020"
    assert _eval_rule(doc_type, rule_id, expired_imp)["status"] == "NON_COMPLIANT"

    # Ausencia de validade (mesmo com data de emissao) -> MANUAL_REVIEW_REQUIRED
    only_emission = base_text + "Emitida em: 01/12/2026"
    assert _eval_rule(doc_type, rule_id, only_emission)["status"] == "MANUAL_REVIEW_REQUIRED"


@pytest.mark.parametrize("doc_type, rule_id, base_text", CERT_TEMPLATES)
def test_missing_cnpj_requires_manual_review_for_cnd_crf_cndt(doc_type, rule_id, base_text):
    """Ausencia de CNPJ (regex_patterns) impede COMPLIANT em CND, CRF e CNDT."""
    without_cnpj = base_text.replace("CNPJ: 12.345.678/0001-90\n", "") + "Valida ate: 30/06/2027"
    res = _eval_rule(doc_type, rule_id, without_cnpj)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"
    assert res["evidence"]["missing_regex_patterns"]


def test_crf_missing_certificate_code_requires_manual_review():
    text = (
        "CAIXA ECONOMICA FEDERAL\n"
        "CERTIFICADO DE REGULARIDADE DO FGTS - CRF\n"
        "CNPJ: 12.345.678/0001-90\n"
        "SITUACAO REGULAR perante o FGTS.\n"
        "Valida ate: 30/06/2027\n"
    )
    res = _eval_rule("CRF_FGTS", "RULE-BNDES-002", text)
    assert res["status"] == "MANUAL_REVIEW_REQUIRED"
    assert "CRF[0-9]{8,14}" in res["evidence"]["missing_regex_patterns"]


@pytest.mark.parametrize(
    "doc_type, rule_id, base_text, prohibitive_phrase",
    [
        # CND Federal
        (
            "CND_FEDERAL",
            "RULE-BNDES-001",
            CERT_TEMPLATES[0].values[2],
            "Constam debitos em cobranca administrativa.",
        ),
        (
            "CND_FEDERAL",
            "RULE-BNDES-001",
            CERT_TEMPLATES[0].values[2],
            "Certifica-se que consta debito inscrito em aberto.",
        ),
        (
            "CND_FEDERAL",
            "RULE-BNDES-001",
            CERT_TEMPLATES[0].values[2],
            "Situacao: POSITIVA COM DEBITOS EXIGIVEIS.",
        ),
        (
            "CND_FEDERAL",
            "RULE-BNDES-001",
            CERT_TEMPLATES[0].values[2],
            "Creditos tributarios com exigibilidade nao suspensa.",
        ),
        (
            "CND_FEDERAL",
            "RULE-BNDES-001",
            CERT_TEMPLATES[0].values[2],
            "Constam pendencias fiscais em aberto.",
        ),
        (
            "CND_FEDERAL",
            "RULE-BNDES-001",
            CERT_TEMPLATES[0].values[2],
            "CERTIDAO POSITIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS.",
        ),
        # CRF FGTS
        (
            "CRF_FGTS",
            "RULE-BNDES-002",
            CERT_TEMPLATES[1].values[2],
            "Ha impedimento para emissao do CRF.",
        ),
        (
            "CRF_FGTS",
            "RULE-BNDES-002",
            CERT_TEMPLATES[1].values[2],
            "Empregador possui debitos com o FGTS.",
        ),
        (
            "CRF_FGTS",
            "RULE-BNDES-002",
            CERT_TEMPLATES[1].values[2],
            "Consta pendencia junto ao FGTS.",
        ),
        (
            "CRF_FGTS",
            "RULE-BNDES-002",
            CERT_TEMPLATES[1].values[2],
            "Empregador inadimplente perante o fundo.",
        ),
        (
            "CRF_FGTS",
            "RULE-BNDES-002",
            CERT_TEMPLATES[1].values[2],
            "Situacao nao regular perante a Caixa.",
        ),
        (
            "CRF_FGTS",
            "RULE-BNDES-002",
            CERT_TEMPLATES[1].values[2],
            "Empregador em processo de regularizacao.",
        ),
        # CNDT Trabalhista
        (
            "CNDT_TRABALHISTA",
            "RULE-BNDES-003",
            CERT_TEMPLATES[2].values[2],
            "Certifica-se que constam debitos inscritos no BNDT.",
        ),
        (
            "CNDT_TRABALHISTA",
            "RULE-BNDES-003",
            CERT_TEMPLATES[2].values[2],
            "CERTIDAO POSITIVA DE DEBITOS TRABALHISTAS.",
        ),
        (
            "CNDT_TRABALHISTA",
            "RULE-BNDES-003",
            CERT_TEMPLATES[2].values[2],
            "Existem debitos trabalhistas inadimplidos.",
        ),
        (
            "CNDT_TRABALHISTA",
            "RULE-BNDES-003",
            CERT_TEMPLATES[2].values[2],
            "Debitos em cobranca judicial.",
        ),
    ],
)
def test_expanded_prohibitive_wordings_are_non_compliant(
    doc_type, rule_id, base_text, prohibitive_phrase
):
    text = f"{base_text}\n{prohibitive_phrase}\nValida ate: 30/06/2027"
    res = _eval_rule(doc_type, rule_id, text)
    assert res["status"] == "NON_COMPLIANT"


def test_negated_prohibitive_phrase_does_not_cause_false_rejection():
    """'Nao constam debitos' em certidao regular nao dispara 'CONSTAM DEBITOS'."""
    text = (
        "PODER JUDICIARIO - JUSTICA DO TRABALHO\n"
        "CERTIDAO NEGATIVA DE DEBITOS TRABALHISTAS\n"
        "CNPJ: 12.345.678/0001-90\n"
        "Certifica-se que nao constam debitos trabalhistas inadimplidos.\n"
        "Valida ate: 30/06/2027\n"
    )
    assert _eval_rule("CNDT_TRABALHISTA", "RULE-BNDES-003", text)["status"] == "COMPLIANT"


def test_parser_and_engine_share_single_validity_source():
    """Parser nao escolhe data arbitrariamente quando ha multiplas datas ou data impossivel."""
    ambiguous = (
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
        "CNPJ: 12.345.678/0001-90\n"
        "Validade 30/06/2030. Valida ate 01/01/2020\n"
    )
    scan = scan_validity_dates(ambiguous)
    assert scan.valid_dates == (date(2030, 6, 30), date(2020, 1, 1))
    parsed = extract_fields_and_evidence(ambiguous)
    assert "data_validade" not in parsed.fields

    impossible = (
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
        "CNPJ: 12.345.678/0001-90\n"
        "Valida ate: 31/02/2026\n"
    )
    assert scan_validity_dates(impossible).invalid_raw_dates == ("31/02/2026",)
    assert "data_validade" not in extract_fields_and_evidence(impossible).fields

    repeated = (
        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS\n"
        "CNPJ: 12.345.678/0001-90\n"
        "Emitida em: 01/01/2025\n"
        "Valida ate: 30/06/2027\n"
        "Validade: 30/06/2027\n"
    )
    parsed_rep = extract_fields_and_evidence(repeated)
    assert parsed_rep.fields["data_validade"].value == "2027-06-30"

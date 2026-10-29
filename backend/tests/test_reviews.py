"""Tests for human Maker-Checker review: identity, segregation and append-only history."""

import pytest

from app.core.config import ApiUser, settings
from app.core.security import hash_api_key
from app.db.models.compliance import AuditLog
from app.db.models.document import Document
from app.db.models.review import ReviewEvent

KEYS = {"ana": "chave-ana-teste", "bruno": "chave-bruno-teste", "carla": "chave-carla-teste"}
JUSTIFICATION = "Laudo conferido contra a certidao original; validade e CNPJ confirmados."
COMMENT = "Conferido de forma independente; de acordo com a proposta."

VALID_CND = (
    "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL\n"
    "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E A DIVIDA ATIVA DA UNIAO\n"
    "Valida ate: 31/12/2099"
)
EXPIRED_CND = VALID_CND.replace("31/12/2099", "01/01/2020")


@pytest.fixture(autouse=True)
def api_users(monkeypatch):
    users = [
        ApiUser(user_id="ana", role="ANALISTA", key_sha256=hash_api_key(KEYS["ana"])),
        ApiUser(user_id="bruno", role="ANALISTA", key_sha256=hash_api_key(KEYS["bruno"])),
        ApiUser(user_id="carla", role="AUDITOR", key_sha256=hash_api_key(KEYS["carla"])),
    ]
    monkeypatch.setattr(settings, "API_USERS", users)


def _as(user):
    return {"X-API-Key": KEYS[user]}


def _evaluated_document(client, db_session, text=VALID_CND, doc_id="doc-review-1"):
    db_session.add(
        Document(
            id=doc_id,
            filename=f"{doc_id}.pdf",
            original_filename=f"{doc_id}.pdf",
            content_type="application/pdf",
            file_size=10,
            storage_path=f"/tmp/{doc_id}.pdf",
            status="COMPLETED",
            extracted_text=text,
        )
    )
    db_session.commit()
    assert client.post(f"/api/v1/compliance/verify/{doc_id}").status_code == 200
    return doc_id


def _propose(client, doc_id, user="ana", decision="APPROVE"):
    return client.post(
        f"/api/v1/compliance/reviews/{doc_id}",
        json={"decision": decision, "justification": JUSTIFICATION},
        headers=_as(user),
    )


def _resolve(client, doc_id, proposal_id, user="bruno", action="confirm"):
    return client.post(
        f"/api/v1/compliance/reviews/{doc_id}/{proposal_id}/{action}",
        json={"comment": COMMENT},
        headers=_as(user),
    )


def test_full_maker_checker_flow_reaches_final_decision(client, db_session):
    doc_id = _evaluated_document(client, db_session)

    proposal = _propose(client, doc_id)
    assert proposal.status_code == 201
    proposal = proposal.json()
    assert proposal["actor_id"] == "ana"
    assert proposal["report_status"] == "COMPLIANT"

    state = client.get(f"/api/v1/compliance/reviews/{doc_id}").json()
    assert state["state"] == "PENDING_CHECK"
    assert state["pending_proposal_id"] == proposal["id"]

    confirmation = _resolve(client, doc_id, proposal["id"])
    assert confirmation.status_code == 201
    assert confirmation.json()["actor_id"] == "bruno"

    state = client.get(f"/api/v1/compliance/reviews/{doc_id}").json()
    assert state["state"] == "FINAL"
    assert state["final_decision"] == "APPROVE"
    assert [e["event_type"] for e in state["events"]] == ["PROPOSED", "CONFIRMED"]


def test_author_cannot_confirm_own_proposal(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    proposal_id = _propose(client, doc_id).json()["id"]

    response = _resolve(client, doc_id, proposal_id, user="ana")

    assert response.status_code == 403
    assert "Segregacao" in response.json()["detail"]
    assert db_session.query(ReviewEvent).count() == 1


def test_author_cannot_return_own_proposal(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    proposal_id = _propose(client, doc_id).json()["id"]
    assert _resolve(client, doc_id, proposal_id, user="ana", action="return").status_code == 403


def test_proposal_cannot_be_resolved_twice(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    proposal_id = _propose(client, doc_id).json()["id"]
    assert _resolve(client, doc_id, proposal_id).status_code == 201

    assert _resolve(client, doc_id, proposal_id, action="return").status_code == 409


def test_only_one_pending_proposal_per_document(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    assert _propose(client, doc_id).status_code == 201
    assert _propose(client, doc_id, user="bruno", decision="REJECT").status_code == 409


def test_returned_proposal_allows_a_new_cycle(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    first = _propose(client, doc_id).json()["id"]
    assert _resolve(client, doc_id, first, action="return").status_code == 201
    assert client.get(f"/api/v1/compliance/reviews/{doc_id}").json()["state"] == "RETURNED"

    second = _propose(client, doc_id, user="bruno", decision="REJECT").json()["id"]
    assert _resolve(client, doc_id, second, user="ana").status_code == 201

    state = client.get(f"/api/v1/compliance/reviews/{doc_id}").json()
    assert state["state"] == "FINAL"
    assert state["final_decision"] == "REJECT"


def test_non_compliant_report_requires_exception_not_approve(client, db_session):
    doc_id = _evaluated_document(client, db_session, text=EXPIRED_CND)

    approve = _propose(client, doc_id, decision="APPROVE")
    assert approve.status_code == 422
    assert "EXCEPTION" in approve.json()["detail"]

    exception = _propose(client, doc_id, decision="EXCEPTION")
    assert exception.status_code == 201
    assert exception.json()["report_status"] == "NON_COMPLIANT"


def test_proposal_requires_existing_report(client, db_session):
    db_session.add(
        Document(
            id="doc-sem-laudo",
            filename="x.pdf",
            original_filename="x.pdf",
            content_type="application/pdf",
            file_size=1,
            storage_path="/tmp/x.pdf",
            status="PROCESSING",
        )
    )
    db_session.commit()
    assert _propose(client, "doc-sem-laudo").status_code == 409


def test_unknown_document_and_proposal_return_404(client, db_session):
    assert _propose(client, "nao-existe").status_code == 404
    assert client.get("/api/v1/compliance/reviews/nao-existe").status_code == 404
    doc_id = _evaluated_document(client, db_session)
    assert _resolve(client, doc_id, "proposta-inexistente").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"decision": "APPROVE", "justification": "curta"},
        {"decision": "APPROVE", "justification": "   " + "x" * 5 + "   "},
        {"decision": "TALVEZ", "justification": JUSTIFICATION},
        {"justification": JUSTIFICATION},
    ],
)
def test_invalid_proposal_payload_is_rejected(client, db_session, payload):
    doc_id = _evaluated_document(client, db_session)
    response = client.post(f"/api/v1/compliance/reviews/{doc_id}", json=payload, headers=_as("ana"))
    assert response.status_code == 422


def test_review_writes_require_personal_key_even_in_test_environment(client, db_session):
    """Sem chave pessoal nao ha autor identificavel: nem anonimo nem a chave de servico."""
    doc_id = _evaluated_document(client, db_session)
    body = {"decision": "APPROVE", "justification": JUSTIFICATION}

    anonymous = client.post(f"/api/v1/compliance/reviews/{doc_id}", json=body)
    service = client.post(
        f"/api/v1/compliance/reviews/{doc_id}", json=body, headers={"X-API-Key": settings.API_KEY}
    )
    invalid = client.post(
        f"/api/v1/compliance/reviews/{doc_id}", json=body, headers={"X-API-Key": "chave-errada"}
    )

    assert anonymous.status_code == 401
    assert service.status_code == 401
    assert invalid.status_code == 401


def test_auditor_can_read_but_not_decide(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    assert _propose(client, doc_id, user="carla").status_code == 403
    assert (
        client.get(f"/api/v1/compliance/reviews/{doc_id}", headers=_as("carla")).status_code == 200
    )


def test_bearer_token_is_accepted_for_personal_key(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    response = client.post(
        f"/api/v1/compliance/reviews/{doc_id}",
        json={"decision": "APPROVE", "justification": JUSTIFICATION},
        headers={"Authorization": f"Bearer {KEYS['ana']}"},
    )
    assert response.status_code == 201


def test_review_events_are_audited_without_key_material(client, db_session):
    doc_id = _evaluated_document(client, db_session)
    proposal_id = _propose(client, doc_id).json()["id"]
    _resolve(client, doc_id, proposal_id)

    audits = (
        db_session.query(AuditLog)
        .filter(AuditLog.action.in_(["REVIEW_PROPOSED", "REVIEW_CONFIRMED"]))
        .order_by(AuditLog.created_at)
        .all()
    )
    assert [(a.action, a.performed_by) for a in audits] == [
        ("REVIEW_PROPOSED", "ana"),
        ("REVIEW_CONFIRMED", "bruno"),
    ]
    assert audits[1].details["proposal_id"] == proposal_id
    assert audits[1].details["decision"] == "APPROVE"
    serialized = str([a.details for a in audits]) + str([a.performed_by for a in audits])
    assert not any(key in serialized for key in KEYS.values())


def test_personal_key_passes_router_auth_in_production(client, db_session, monkeypatch):
    """Em producao a chave pessoal precisa ser aceita tambem pela autenticacao do roteador."""
    doc_id = _evaluated_document(client, db_session)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    assert client.get(f"/api/v1/compliance/reviews/{doc_id}").status_code == 401
    assert (
        client.get(f"/api/v1/compliance/reviews/{doc_id}", headers=_as("carla")).status_code == 200
    )
    assert client.get("/api/v1/compliance/rules", headers=_as("ana")).status_code == 200

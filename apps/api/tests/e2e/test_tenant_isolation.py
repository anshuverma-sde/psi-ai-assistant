"""MANDATORY: one organization's knowledge must never reach another organization."""

import pytest

from tests.conftest import assistant_token, register_org, upload
from tests.e2e.test_auth_and_format import assert_error
from tests.pdf_factory import make_pdf

ORG_A_DOC = ("Merit Scholarship rules.\nStudents need a cumulative GPA of at least 3.5 for the Merit Scholarship.\n"
             "Merit Scholarship applications close on March 15.")
ORG_B_DOC = ("Leave policy.\nEmployees receive 20 days of paid annual leave per year.\n"
             "Employees receive 10 days of paid sick leave per year.")


@pytest.fixture
async def two_orgs(app):
    a = await register_org(app, "Org A University")
    b = await register_org(app, "Org B Corp")
    doc_a = (await upload(a, "A_Scholarships.pdf", make_pdf([ORG_A_DOC]))).json()["data"]
    doc_b = (await upload(b, "B_Leave.pdf", make_pdf([ORG_B_DOC]))).json()["data"]
    return {"a": a, "b": b, "doc_a": doc_a, "doc_b": doc_b,
            "token_a": await assistant_token(a), "token_b": await assistant_token(b)}


async def _ask(client, token, q):
    return (await client.post("/api/ask", json={"token": token, "question": q})).json()["data"]


async def test_assistant_only_answers_from_its_own_documents(two_orgs, client):
    # Org B's assistant asked about Org A's content → refuses, cites nothing from A.
    data = await _ask(client, two_orgs["token_b"], "What GPA do I need for the merit scholarship?")
    assert data["status"] == "no_answer"
    assert all(s["document"] != "A_Scholarships.pdf" for s in data["sources"])

    # Org A's assistant asked about Org B's content → refuses too.
    data = await _ask(client, two_orgs["token_a"], "How many days of sick leave do employees get?")
    assert data["status"] == "no_answer"

    # Each assistant answers its own question, citing only its own document.
    a = await _ask(client, two_orgs["token_a"], "When do merit scholarship applications close?")
    b = await _ask(client, two_orgs["token_b"], "How many days of annual leave do employees get?")
    assert a["status"] == b["status"] == "answered"
    assert {s["document"] for s in a["sources"]} == {"A_Scholarships.pdf"}
    assert {s["document"] for s in b["sources"]} == {"B_Leave.pdf"}
    assert {s["document_id"] for s in a["sources"]} == {two_orgs["doc_a"]["id"]}


async def test_admin_cannot_access_other_orgs_documents(two_orgs):
    b, doc_a = two_orgs["b"], two_orgs["doc_a"]["id"]
    assert_error(await b.get(f"/api/admin/documents/{doc_a}"), 404, "NOT_FOUND")
    assert_error(await b.delete(f"/api/admin/documents/{doc_a}"), 404, "NOT_FOUND")
    assert_error(await b.put(f"/api/admin/documents/{doc_a}",
                             files={"file": ("x.pdf", make_pdf(["hijack"]), "application/pdf")}), 404, "NOT_FOUND")
    names = [d["original_name"] for d in (await b.get("/api/admin/documents")).json()["data"]["documents"]]
    assert names == ["B_Leave.pdf"]
    # Org A's document is untouched.
    assert (await two_orgs["a"].get(f"/api/admin/documents/{doc_a}")).json()["data"]["status"] == "READY"


async def test_assistant_token_cannot_access_admin_api(two_orgs, client):
    token = two_orgs["token_a"]
    for path in ("/api/admin/documents", "/api/admin/assistant", "/api/admin/usage", "/api/auth/me"):
        assert_error(await client.get(path, headers={"Authorization": f"Bearer {token}"}), 401, "UNAUTHORIZED")
        assert_error(await client.get(path, cookies={"psi_session": token}), 401, "UNAUTHORIZED")


async def test_regenerated_token_invalidates_old_one(two_orgs, client):
    a, old = two_orgs["a"], two_orgs["token_a"]
    new = (await a.post("/api/admin/assistant/regenerate")).json()["data"]["token"]
    assert new != old
    assert_error(await client.post("/api/ask", json={"token": old, "question": "Merit GPA?"}), 401, "TOKEN_INVALID")
    assert (await _ask(client, new, "When do merit scholarship applications close?"))["status"] == "answered"


async def test_public_assistant_info_exposes_no_documents(two_orgs, client):
    body = (await client.get(f"/api/public/assistant/{two_orgs['token_a']}")).json()["data"]
    assert body == {"organization_name": "Org A University", "ready": True,
                    "suggested_questions": ["What does the A Scholarships document cover?"]}
    assert_error(await client.get("/api/public/assistant/ast_invalidtokeninvalidtokeninvalidtoken00000"),
                 401, "TOKEN_INVALID")

"""The question pipeline end-to-end (real retrieval + System 1, scripted LLM)."""

from tests.conftest import assistant_token, register_org, upload
from tests.e2e.test_auth_and_format import assert_error
from tests.pdf_factory import make_pdf

SCHOLARSHIP = (
    "Merit Scholarship eligibility requirements.\n"
    "Students must be in their second year of study or above to receive the Merit Scholarship.\n"
    "Students must have a cumulative GPA of at least 3.5 for the Merit Scholarship.\n"
    "Merit Scholarship applications close on March 15 each year."
)
TIERS = "Merit Scholarship award tiers.\nSilver tier: GPA 3.50 to 3.79, $2,000 per year.\nGold tier: GPA 3.80 to 4.00."

MERIT_PLAN = {
    "needs_decisions": True,
    "subject": "Merit Scholarship",
    "facts": [{"key": "year_of_study", "value": 2}, {"key": "gpa", "value": 3.7}],
    "decisions": [
        {"kind": "boolean", "id": "d1", "question": "Year requirement met?",
         "conditions": [{"id": "c1", "label": "Second year or above", "fact": "year_of_study", "op": "gte",
                         "value": 2, "source_id": "s1"}]},
        {"kind": "boolean", "id": "d2", "question": "GPA requirement met?",
         "conditions": [{"id": "c2", "label": "GPA of at least 3.5", "fact": "gpa", "op": "gte",
                         "value": 3.5, "source_id": "s1"}]},
        {"kind": "choice", "id": "d3", "question": "Which tier applies?",
         "options": [{"label": "Gold", "when": [{"id": "c3", "label": "GPA >= 3.8", "fact": "gpa", "op": "gte",
                                                 "value": 3.8, "source_id": "s1"}]},
                     {"label": "Silver", "when": [{"id": "c4", "label": "GPA >= 3.5", "fact": "gpa", "op": "gte",
                                                   "value": 3.5, "source_id": "s1"}]}]},
    ],
}


async def make_assistant(app):
    org = await register_org(app, "Northbridge Test")
    await upload(org, "Scholarship_Rules.pdf", make_pdf([SCHOLARSHIP, TIERS]))
    return org, await assistant_token(org)


async def ask(client, token, question, previous_question=None):
    body = {"token": token, "question": question}
    if previous_question:
        body["previous_question"] = previous_question
    return await client.post("/api/ask", json=body)


async def test_input_errors(app, client):
    _, token = await make_assistant(app)
    assert_error(await ask(client, token, "   "), 400, "QUESTION_EMPTY")
    assert_error(await ask(client, token, "x" * 1001), 400, "QUESTION_TOO_LONG")
    assert_error(await ask(client, "ast_" + "a" * 43, "hi"), 401, "TOKEN_INVALID")
    assert_error(await ask(client, "garbage", "hi"), 401, "TOKEN_INVALID")


async def test_empty_knowledge_base(app, client):
    org = await register_org(app, "Empty Org")
    body = (await ask(client, await assistant_token(org), "What is the leave policy?")).json()["data"]
    assert body["status"] == "no_answer" and "knowledge_base_empty" in body["notices"]


async def test_direct_question_is_grounded(app, client, fake_llm):
    _, token = await make_assistant(app)
    data = (await ask(client, token, "When is the merit scholarship application deadline?")).json()["data"]
    assert data["status"] == "answered"
    assert data["sources"][0]["document"] == "Scholarship_Rules.pdf" and data["sources"][0]["page"] in (1, 2)
    assert data["verdict"] is None and data["decisions"] == []
    assert {"classify", "retrieve", "gate", "generate"} <= set(data["timings_ms"])


async def test_out_of_scope_question_skips_llm(app, client, fake_llm):
    _, token = await make_assistant(app)
    calls_before = len(fake_llm.calls)
    data = (await ask(client, token, "What is the weather forecast in Paris tomorrow?")).json()["data"]
    assert data["status"] == "no_answer" and data["sources"] == []
    assert len(fake_llm.calls) == calls_before  # refused by the System 1 gate, no LLM call


async def test_multi_decision_question(app, client, fake_llm):
    _, token = await make_assistant(app)
    fake_llm.queue_plan(MERIT_PLAN)
    data = (await ask(client, token, "I'm a second-year student with a 3.7 GPA. Am I eligible for the "
                                     "merit scholarship and which tier?")).json()["data"]
    assert data["status"] == "answered"
    assert data["verdict"]["outcome"] == "ELIGIBLE"
    assert data["verdict"]["qualifiers"] == {"Which tier applies?": "Silver"}
    assert [d["id"] for d in data["decisions"]] == ["d1", "d2", "d3"]
    assert {d["evaluator"] for d in data["decisions"]} == {"system1.boolean_rules", "system1.choice_rules"}
    # each decision ran as its own parallel graph branch
    assert {"evaluate:d1", "evaluate:d2", "evaluate:d3", "combine", "decompose"} <= set(data["timings_ms"])


async def test_missing_facts_ask_for_info(app, client, fake_llm):
    _, token = await make_assistant(app)
    plan = {**MERIT_PLAN, "facts": [], "decisions": MERIT_PLAN["decisions"][:2]}
    fake_llm.queue_plan(plan)
    data = (await ask(client, token, "Am I eligible for the merit scholarship?")).json()["data"]
    assert data["status"] == "needs_info"
    assert data["verdict"]["missing_facts"] == ["gpa", "year_of_study"]


async def test_follow_up_answers_the_original_question(app, client, fake_llm):
    _, token = await make_assistant(app)
    original = "Am I eligible for the merit scholarship?"

    # 1st turn: no facts given → the engine asks for them.
    fake_llm.queue_plan({**MERIT_PLAN, "facts": [], "decisions": MERIT_PLAN["decisions"][:2]})
    first = (await ask(client, token, original)).json()["data"]
    assert first["status"] == "needs_info" and first["resolved_question"] == original

    # 2nd turn: the visitor only types the missing details; the server answers the combined question.
    fake_llm.queue_plan(MERIT_PLAN)
    second = (await ask(client, token, "second year, GPA 3.7", previous_question=first["resolved_question"])).json()["data"]
    assert second["resolved_question"] == f"{original} Additional details: second year, GPA 3.7"
    assert second["status"] == "answered" and second["verdict"]["outcome"] == "ELIGIBLE"
    decompose_prompt = fake_llm.prompts[-2]  # last call is the answer writer; the one before is decomposition
    assert original in decompose_prompt and "GPA 3.7" in decompose_prompt


async def test_follow_up_still_validates_the_new_message(app, client):
    _, token = await make_assistant(app)
    assert_error(await ask(client, token, "   ", previous_question="Am I eligible?"), 400, "QUESTION_EMPTY")


async def test_ungrounded_plan_is_rejected(app, client, fake_llm):
    _, token = await make_assistant(app)
    bad = {**MERIT_PLAN, "decisions": [{**MERIT_PLAN["decisions"][0], "conditions": [
        {**MERIT_PLAN["decisions"][0]["conditions"][0], "source_id": "s99"}]}]}
    fake_llm.queue_plan(bad)
    fake_llm.queue_plan(bad)  # the repair attempt also cites an unknown source
    data = (await ask(client, token, "Am I eligible for the merit scholarship as a 2nd year?")).json()["data"]
    assert data["status"] == "needs_review" and "decomposition_invalid" in data["notices"]


async def test_llm_outage_falls_back_gracefully(app, client, fake_llm):
    _, token = await make_assistant(app)
    fake_llm.unavailable = True
    try:
        data = (await ask(client, token, "When is the merit scholarship application deadline?")).json()["data"]
    finally:
        fake_llm.unavailable = False
    assert data["status"] == "needs_review" and "llm_unavailable" in data["notices"]
    assert data["sources"] and data["sources"][0]["document"] == "Scholarship_Rules.pdf"


async def test_usage_counts(app, client):
    org, token = await make_assistant(app)
    await ask(client, token, "When is the merit scholarship application deadline?")
    await ask(client, token, "What is the weather forecast in Paris tomorrow?")
    usage = (await org.get("/api/admin/usage")).json()["data"]
    assert usage["total_questions"] == 2 and usage["answered"] == 1 and usage["no_answer"] == 1

"""System 1 evaluators + combiner: pure, deterministic, no I/O."""

import pytest

from app.modules.reasoning.decisions.combiner import combine_results
from app.modules.reasoning.decisions.conditions import evaluate_condition, to_number
from app.modules.reasoning.decisions.engine import evaluate_task
from app.modules.reasoning.decisions.types import (
    BooleanTask,
    ChoiceOption,
    ChoiceTask,
    Condition,
    DecisionPlan,
    ScoreFactor,
    ScoreTask,
)


def cond(fact, op, value=None, cid="c1", label=None):
    return Condition(id=cid, label=label or f"{fact} {op} {value}", fact=fact, op=op, value=value, source_id="s1")


@pytest.mark.parametrize("fact_value, op, expected, result", [
    (3.7, "gte", 3.5, "TRUE"),
    (3.4, "gte", 3.5, "FALSE"),
    ("3.7", "gte", 3.5, "TRUE"),          # numeric strings are coerced
    ("2nd", "gte", 2, "TRUE"),
    (True, "is_false", None, "FALSE"),
    ("yes", "is_true", None, "TRUE"),
    ("Hybrid", "eq", "hybrid", "TRUE"),    # case-insensitive strings
    ("warehouse", "in", ["warehouse", "lab"], "TRUE"),
    ("office", "not_in", ["warehouse", "lab"], "TRUE"),
    ("lots", "gt", 3, "UNKNOWN"),          # incomparable → UNKNOWN, never a guess
])
def test_condition_comparator(fact_value, op, expected, result):
    trace = evaluate_condition(cond("x", op, expected), {"x": fact_value})
    assert trace.result == result


def test_missing_fact_is_unknown():
    assert evaluate_condition(cond("gpa", "gte", 3.5), {}).result == "UNKNOWN"


def test_to_number_rejects_free_text():
    assert to_number("about three and a half") is None
    assert to_number("$2,000") == 2000


def merit_task():
    return BooleanTask(kind="boolean", id="d1", question="Meets merit requirements?", conditions=[
        cond("year_of_study", "gte", 2, "c1", "Second year or above"),
        cond("gpa", "gte", 3.5, "c2", "GPA at least 3.5"),
    ])


def test_boolean_all_true():
    r = evaluate_task(merit_task(), {"year_of_study": 2, "gpa": 3.7})
    assert (r.outcome, r.passed, r.confidence) == ("TRUE", True, 1.0)


def test_boolean_false_is_decisive_even_with_missing_facts():
    r = evaluate_task(merit_task(), {"year_of_study": 1})
    assert r.outcome == "FALSE" and r.missing_facts == []


def test_boolean_unknown_reports_missing_facts():
    r = evaluate_task(merit_task(), {"year_of_study": 2})
    assert r.outcome == "UNKNOWN" and r.passed is None and r.missing_facts == ["gpa"]


def test_boolean_any_combinator():
    task = BooleanTask(kind="boolean", id="d1", question="Rule or exception?", combinator="any",
                       conditions=[cond("a", "is_true", cid="c1"), cond("b", "is_true", cid="c2")])
    assert evaluate_task(task, {"a": False, "b": True}).outcome == "TRUE"


def tier_task():
    return ChoiceTask(kind="choice", id="d2", question="Which tier?", options=[
        ChoiceOption(label="Gold", when=[cond("gpa", "gte", 3.8, "c3")]),
        ChoiceOption(label="Silver", when=[cond("gpa", "gte", 3.5, "c4"), cond("gpa", "lt", 3.8, "c5")]),
    ])


@pytest.mark.parametrize("gpa, tier", [(3.9, "Gold"), (3.7, "Silver"), (3.2, "NONE")])
def test_choice(gpa, tier):
    assert evaluate_task(tier_task(), {"gpa": gpa}).outcome == tier


def test_choice_unknown_without_fact():
    r = evaluate_task(tier_task(), {})
    assert r.outcome == "UNKNOWN" and r.missing_facts == ["gpa"]


def test_choice_catch_all_option_becomes_default():
    task = ChoiceTask.model_validate({"kind": "choice", "id": "d2", "question": "Which tier?", "options": [
        {"label": "Gold", "when": [cond("gpa", "gte", 3.8).model_dump()]},
        {"label": "No tier", "when": []},
    ]})
    assert task.default == "No tier" and [o.label for o in task.options] == ["Gold"]
    assert evaluate_task(task, {"gpa": 3.0}).outcome == "No tier"
    assert evaluate_task(task, {"gpa": 3.9}).outcome == "Gold"


def test_score_weighted():
    task = ScoreTask(kind="score", id="d3", question="Strength?", threshold=0.6, factors=[
        ScoreFactor(weight=3, condition=cond("gpa", "gte", 3.5, "c6")),
        ScoreFactor(weight=1, condition=cond("volunteer", "is_true", cid="c7")),
    ])
    r = evaluate_task(task, {"gpa": 3.9, "volunteer": False})
    assert r.score == 0.75 and r.outcome == "STRONG" and r.passed is True
    r = evaluate_task(task, {"volunteer": True})
    assert r.passed is None and r.confidence == 0.25


def test_combiner_verdicts():
    ok = evaluate_task(merit_task(), {"year_of_study": 3, "gpa": 3.6})
    tier = evaluate_task(tier_task(), {"gpa": 3.6})
    assert combine_results([ok, tier]).outcome == "ELIGIBLE"
    assert combine_results([ok, tier]).qualifiers == {"Which tier?": "Silver"}

    failed = evaluate_task(merit_task(), {"year_of_study": 1, "gpa": 3.9})
    verdict = combine_results([failed])
    assert verdict.outcome == "NOT_ELIGIBLE" and verdict.unmet == ["Second year or above"]

    unknown = evaluate_task(merit_task(), {})
    verdict = combine_results([unknown])
    assert verdict.outcome == "NEEDS_INFO" and verdict.missing_facts == ["gpa", "year_of_study"]


def test_derived_outcome_conditions_are_pruned():
    from app.modules.reasoning.understanding.decomposer import prune_derived_conditions

    plan = DecisionPlan.model_validate({
        "facts": [{"key": "months_of_service", "value": 14}, {"key": "remote_days_per_week", "value": 3}],
        "decisions": [
            {"kind": "boolean", "id": "d1", "question": "Remote eligible?", "conditions": [
                cond("months_of_service", "gte", 12, "c1").model_dump()]},
            {"kind": "boolean", "id": "d2", "question": "Stipend?", "conditions": [
                cond("remote_days_per_week", "gte", 2, "c2").model_dump(),
                cond("is_remote_eligible", "is_true", cid="c3", label="Employee is remote-eligible").model_dump()]},
        ],
    })
    pruned = prune_derived_conditions(plan)
    assert [c.id for c in pruned.decisions[1].conditions] == ["c2"]
    assert combine_results([evaluate_task(d, pruned.fact_map()) for d in pruned.decisions]).outcome == "ELIGIBLE"


def test_stated_facts_are_never_pruned():
    from app.modules.reasoning.understanding.decomposer import prune_derived_conditions

    plan = DecisionPlan.model_validate({
        "facts": [{"key": "eligible_for_grant", "value": False}],
        "decisions": [
            {"kind": "boolean", "id": "d1", "question": "a", "conditions": [cond("x", "is_true", cid="c1").model_dump()]},
            {"kind": "boolean", "id": "d2", "question": "b", "conditions": [
                cond("eligible_for_grant", "is_false", cid="c2").model_dump()]},
        ],
    })
    assert len(prune_derived_conditions(plan).decisions) == 2


def test_plan_parses_llm_json_and_normalizes_keys():
    plan = DecisionPlan.model_validate({
        "facts": [{"key": "Year Of Study", "value": 2}],
        "decisions": [{"kind": "boolean", "id": "d1", "question": "q",
                       "conditions": [{"id": "c1", "label": "l", "fact": "year-of-study", "op": "gte",
                                       "value": 2, "source_id": "s1"}]}],
    })
    assert plan.fact_map() == {"year_of_study": 2}
    assert plan.all_conditions()[0].fact == "year_of_study"

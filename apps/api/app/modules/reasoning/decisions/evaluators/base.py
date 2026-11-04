from typing import Protocol

from app.modules.reasoning.decisions.types import ConditionTrace, DecisionResult, Scalar


class DecisionEvaluator(Protocol):
    """A System 1 model: fast, deterministic, typed input → typed output. No LLM calls."""

    kind: str
    name: str

    def evaluate(self, task, facts: dict[str, Scalar]) -> DecisionResult: ...


def missing_facts(traces: list[ConditionTrace]) -> list[str]:
    return sorted({t.fact for t in traces if t.result == "UNKNOWN" and t.actual is None})


def source_ids(traces: list[ConditionTrace]) -> list[str]:
    return sorted({t.source_id for t in traces})


def known_fraction(traces: list[ConditionTrace]) -> float:
    return round(sum(t.result != "UNKNOWN" for t in traces) / len(traces), 2) if traces else 0.0

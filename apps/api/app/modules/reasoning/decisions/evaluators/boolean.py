from app.modules.reasoning.decisions.conditions import combine_all, combine_any, evaluate_condition
from app.modules.reasoning.decisions.evaluators.base import known_fraction, missing_facts, source_ids
from app.modules.reasoning.decisions.types import BooleanTask, DecisionResult, Scalar


class BooleanRuleEvaluator:
    """Is the requirement met? TRUE / FALSE / UNKNOWN over AND/OR-combined conditions."""

    kind = "boolean"
    name = "system1.boolean_rules"

    def evaluate(self, task: BooleanTask, facts: dict[str, Scalar]) -> DecisionResult:
        traces = [evaluate_condition(c, facts) for c in task.conditions]
        combine = combine_all if task.combinator == "all" else combine_any
        outcome = combine([t.result for t in traces])
        decided = outcome != "UNKNOWN"
        return DecisionResult(
            id=task.id,
            kind="boolean",
            question=task.question,
            evaluator=self.name,
            outcome=outcome,
            passed=None if not decided else outcome == "TRUE",
            confidence=1.0 if decided else known_fraction(traces),
            required=task.required,
            trace=traces,
            missing_facts=[] if decided else missing_facts(traces),
            source_ids=source_ids(traces),
        )

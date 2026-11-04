from app.modules.reasoning.decisions.conditions import combine_all, evaluate_condition
from app.modules.reasoning.decisions.evaluators.base import missing_facts, source_ids
from app.modules.reasoning.decisions.types import ChoiceTask, ConditionTrace, DecisionResult, Scalar


class ChoiceRuleEvaluator:
    """Which category/tier applies? First option whose conditions all hold wins."""

    kind = "choice"
    name = "system1.choice_rules"

    def evaluate(self, task: ChoiceTask, facts: dict[str, Scalar]) -> DecisionResult:
        all_traces: list[ConditionTrace] = []
        selected: str | None = None
        undetermined: list[ConditionTrace] = []

        for option in task.options:
            traces = [evaluate_condition(c, facts, group=option.label) for c in option.when]
            all_traces += traces
            result = combine_all([t.result for t in traces])
            if result == "TRUE" and selected is None:
                selected = option.label
            elif result == "UNKNOWN":
                undetermined += traces

        if selected is not None:
            outcome, passed, confidence, missing = selected, True, 1.0, []
        elif undetermined:
            outcome, passed, confidence, missing = "UNKNOWN", None, 0.5, missing_facts(undetermined)
        else:
            outcome = task.default or "NONE"
            passed, confidence, missing = task.default is not None, 1.0, []

        return DecisionResult(
            id=task.id,
            kind="choice",
            question=task.question,
            evaluator=self.name,
            outcome=outcome,
            passed=passed,
            confidence=confidence,
            required=task.required,
            trace=all_traces,
            missing_facts=missing,
            source_ids=source_ids(all_traces),
        )

from app.modules.reasoning.decisions.conditions import evaluate_condition
from app.modules.reasoning.decisions.evaluators.base import missing_facts, source_ids
from app.modules.reasoning.decisions.types import DecisionResult, Scalar, ScoreTask


def strength_label(score: float) -> str:
    if score >= 0.75:
        return "STRONG"
    if score >= 0.5:
        return "MODERATE"
    return "WEAK"


class WeightedScoreEvaluator:
    """How strongly does the policy support the outcome? Weighted share of satisfied factors (0..1)."""

    kind = "score"
    name = "system1.weighted_score"

    def evaluate(self, task: ScoreTask, facts: dict[str, Scalar]) -> DecisionResult:
        traces = [evaluate_condition(f.condition, facts) for f in task.factors]
        weights = [f.weight for f in task.factors]
        total = sum(weights)
        met = sum(w for w, t in zip(weights, traces, strict=True) if t.result == "TRUE")
        unknown = sum(w for w, t in zip(weights, traces, strict=True) if t.result == "UNKNOWN")

        score = round(met / total, 2)
        best_case = (met + unknown) / total
        if score >= task.threshold:
            passed: bool | None = True
        elif best_case < task.threshold:
            passed = False
        else:
            passed = None  # could go either way depending on missing facts

        return DecisionResult(
            id=task.id,
            kind="score",
            question=task.question,
            evaluator=self.name,
            outcome=strength_label(score),
            passed=passed,
            score=score,
            confidence=round(1 - unknown / total, 2),
            required=task.required,
            trace=traces,
            missing_facts=missing_facts(traces) if passed is None else [],
            source_ids=source_ids(traces),
        )

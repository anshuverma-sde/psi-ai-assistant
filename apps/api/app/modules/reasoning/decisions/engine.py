"""Dispatches each decision task to its System 1 evaluator."""

import logging

from app.core.utils.timing import stopwatch
from app.modules.reasoning.decisions.evaluators.base import DecisionEvaluator
from app.modules.reasoning.decisions.evaluators.boolean import BooleanRuleEvaluator
from app.modules.reasoning.decisions.evaluators.choice import ChoiceRuleEvaluator
from app.modules.reasoning.decisions.evaluators.score import WeightedScoreEvaluator
from app.modules.reasoning.decisions.types import DecisionResult, DecisionTask, Scalar

logger = logging.getLogger(__name__)

EVALUATORS: dict[str, DecisionEvaluator] = {
    e.kind: e for e in (BooleanRuleEvaluator(), ChoiceRuleEvaluator(), WeightedScoreEvaluator())
}


class DecisionEvaluationError(Exception):
    pass


def evaluate_task(task: DecisionTask, facts: dict[str, Scalar]) -> DecisionResult:
    evaluator = EVALUATORS.get(task.kind)
    if evaluator is None:
        raise DecisionEvaluationError(f"No evaluator for decision kind '{task.kind}'")
    try:
        with stopwatch() as t:
            result = evaluator.evaluate(task, facts)
    except Exception as exc:  # an evaluator bug must not take the whole answer down
        logger.exception("Evaluator %s failed on %s", evaluator.name, task.id)
        raise DecisionEvaluationError(str(exc)) from exc
    result.duration_ms = t["ms"]
    return result

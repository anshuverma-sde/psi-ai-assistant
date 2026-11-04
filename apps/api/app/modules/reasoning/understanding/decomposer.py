"""LLM step #1: natural-language question + evidence → typed DecisionPlan."""

import logging
import re

from app.infra.llm.base import ChatMessage, LLMOutputError, LLMProvider, complete_structured
from app.modules.reasoning.context import EvidenceContext
from app.modules.reasoning.decisions.types import BooleanTask, DecisionPlan
from app.modules.reasoning.understanding.prompts.decompose import DECOMPOSE_SYSTEM, decompose_user_prompt

logger = logging.getLogger(__name__)


class PlanValidationError(Exception):
    pass


def validate_plan(plan: DecisionPlan, context: EvidenceContext) -> DecisionPlan:
    """Rejects plans that cite evidence we never retrieved (ungrounded rules)."""
    bad = sorted({c.source_id for c in plan.all_conditions() if c.source_id not in context})
    if bad:
        raise PlanValidationError(f"Conditions cite unknown sources: {', '.join(bad)}")
    ids = [d.id for d in plan.decisions]
    if len(ids) != len(set(ids)):
        raise PlanValidationError("Duplicate decision ids")
    return plan


# Facts that name an *outcome* ("remote_eligible", "meets_requirements") rather than something about the user.
_DERIVED_OUTCOME = re.compile(r"eligib|qualif|requirement|criteria|^meets?_|_satisfied$", re.I)


def prune_derived_conditions(plan: DecisionPlan) -> DecisionPlan:
    """Removes conditions that chain one decision onto another's outcome.

    Decisions must be independent; the combiner already requires every required decision to hold,
    so a condition like "employee is remote-eligible" is redundant — and, since the user never states
    it as a fact, it would wrongly evaluate to UNKNOWN. Facts the user actually stated are never pruned.
    """
    stated = set(plan.fact_map())
    required_booleans = [d for d in plan.decisions if isinstance(d, BooleanTask) and d.required]
    if len(required_booleans) < 2:
        return plan

    for task in required_booleans:
        kept = [c for c in task.conditions
                if c.fact in stated or not (_DERIVED_OUTCOME.search(c.fact) or _DERIVED_OUTCOME.search(c.label))]
        if len(kept) != len(task.conditions):
            logger.info("Pruned %s derived-outcome condition(s) from %s",
                        len(task.conditions) - len(kept), task.id)
        task.conditions = kept
    plan.decisions = [d for d in plan.decisions if not (isinstance(d, BooleanTask) and not d.conditions)]
    return plan


class QuestionDecomposer:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def decompose(self, question: str, context: EvidenceContext) -> DecisionPlan:
        messages = [
            ChatMessage("system", DECOMPOSE_SYSTEM),
            ChatMessage("user", decompose_user_prompt(question, context.render())),
        ]
        plan = await complete_structured(self.llm, messages, DecisionPlan, max_tokens=2000)
        try:
            return prune_derived_conditions(validate_plan(plan, context))
        except PlanValidationError as exc:
            raise LLMOutputError(str(exc)) from exc

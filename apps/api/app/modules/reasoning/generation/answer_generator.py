"""LLM step #2: evidence (+ authoritative decision result) → grounded natural-language answer."""

import json

from pydantic import BaseModel, Field

from app.infra.llm.base import ChatMessage, LLMProvider, complete_structured
from app.modules.reasoning.context import EvidenceContext
from app.modules.reasoning.decisions.types import DecisionResult, Verdict
from app.modules.reasoning.generation.prompts.answer import (
    ANSWER_SYSTEM,
    COMPARISON_RULES,
    DECISION_RULES,
    answer_user_prompt,
)


class GeneratedAnswer(BaseModel):
    answerable: bool
    answer: str = ""
    citations: list[str] = Field(default_factory=list)


def decision_block(verdict: Verdict, results: list[DecisionResult]) -> str:
    payload = {
        "outcome": verdict.outcome,
        "subject": verdict.subject,
        "summary": verdict.summary,
        "missing_information": verdict.missing_facts,
        "checks": [
            {
                "question": r.question,
                "kind": r.kind,
                "result": r.outcome if r.score is None else f"{r.outcome} (score {r.score})",
                "conditions": [
                    {"condition": t.label, "user_value": t.actual, "result": t.result, "source": t.source_id}
                    for t in r.trace
                ],
            }
            for r in sorted(results, key=lambda r: r.id)
        ],
    }
    return json.dumps(payload, indent=2, default=str)


class AnswerGenerator:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def generate(
        self,
        *,
        org_name: str,
        question: str,
        question_type: str,
        context: EvidenceContext,
        verdict: Verdict | None,
        results: list[DecisionResult],
    ) -> GeneratedAnswer:
        rules = []
        if verdict is not None:
            rules.append(DECISION_RULES)
        if question_type == "comparison":
            rules.append(COMPARISON_RULES)
        system = ANSWER_SYSTEM.format(org_name=org_name, decision_rules="\n".join(rules))
        user = answer_user_prompt(
            question, context.render(), decision_block(verdict, results) if verdict else None
        )
        return await complete_structured(
            self.llm, [ChatMessage("system", system), ChatMessage("user", user)], GeneratedAnswer,
            max_tokens=900,
        )

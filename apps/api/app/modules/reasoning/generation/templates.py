"""Deterministic answer texts — used when no LLM call is needed or the LLM is unavailable."""

from app.modules.reasoning.context import EvidenceContext
from app.modules.reasoning.decisions.types import DecisionResult, Verdict

NO_ANSWER = (
    "I couldn't find this in {org}'s knowledge base, so I can't answer it reliably. "
    "Please contact {org} directly for help with this question."
)
KB_EMPTY = "{org}'s assistant doesn't have any documents yet. Please check back later."

_VERDICT_HEADLINES = {
    "ELIGIBLE": "Based on the policy, you meet all the requirements",
    "NOT_ELIGIBLE": "Based on the policy, you do not meet all the requirements",
    "NEEDS_INFO": "I need a bit more information to decide",
    "INFORMATIONAL": "Here is what the policy says for your situation",
}
_RESULT_ICON = {"TRUE": "✅", "FALSE": "❌", "UNKNOWN": "❔"}


def verdict_answer(verdict: Verdict, results: list[DecisionResult]) -> tuple[str, list[str]]:
    """Readable answer built purely from the structured decision results."""
    subject = f" for {verdict.subject}" if verdict.subject else ""
    lines = [f"**{_VERDICT_HEADLINES[verdict.outcome]}{subject}.** {verdict.summary}", ""]
    cited: list[str] = []
    for result in sorted(results, key=lambda r: r.id):
        if result.kind == "boolean":
            for t in result.trace:
                lines.append(f"- {_RESULT_ICON[t.result]} {t.label} [{t.source_id}]")
                cited.append(t.source_id)
        else:
            value = f"{result.outcome} ({result.score:.2f})" if result.score is not None else result.outcome
            src = result.source_ids[0] if result.source_ids else None
            lines.append(f"- {result.question}: **{value}**" + (f" [{src}]" if src else ""))
            if src:
                cited.append(src)
    if verdict.missing_facts:
        lines += ["", "Please tell me: " + ", ".join(m.replace("_", " ") for m in verdict.missing_facts) + "."]
    return "\n".join(lines), list(dict.fromkeys(cited))


def excerpts_answer(context: EvidenceContext, limit: int = 3) -> tuple[str, list[str]]:
    lines = ["The assistant is busy right now, so here are the most relevant passages from the documents. "
             "Please try again in a few minutes for a full answer.", ""]
    ids = []
    for ref in context.refs[:limit]:
        text = " ".join(ref.chunk.text.split())[:280]
        lines.append(f"- “{text}…” [{ref.sid}]")
        ids.append(ref.sid)
    return "\n".join(lines), ids

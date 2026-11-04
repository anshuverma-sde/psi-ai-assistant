import json
from collections import deque

from app.infra.llm.base import ChatMessage, LLMUnavailableError


class FakeLLM:
    """Scripted LLM: deterministic plans/answers so tests never hit the network."""

    name = "fake"

    def __init__(self) -> None:
        self.plans: deque[dict] = deque()
        self.unavailable = False
        self.calls: list[str] = []
        self.prompts: list[str] = []  # last user message of each call

    def queue_plan(self, plan: dict) -> None:
        self.plans.append(plan)

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False,
                       temperature: float = 0.0, max_tokens: int = 1500) -> str:
        system = messages[0].content
        kind = "decompose" if "STRUCTURED DECISION PLAN" in system else "answer"
        self.calls.append(kind)
        self.prompts.append(messages[-1].content)
        if self.unavailable:
            raise LLMUnavailableError("fake outage")
        if kind == "decompose":
            plan = self.plans.popleft() if self.plans else {"needs_decisions": False, "facts": [], "decisions": []}
            return json.dumps(plan)
        has_decision = "DECISION RESULT" in messages[-1].content
        answer = "Per the decision engine, see the checks below [s1]." if has_decision else "Answer from documents [s1]."
        return json.dumps({"answerable": True, "answer": answer, "citations": ["s1"]})

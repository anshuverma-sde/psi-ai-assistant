from typing import Literal

from pydantic import BaseModel, Field

from app.modules.reasoning.decisions.types import DecisionResult, Verdict
from app.modules.reasoning.generation.citation_validator import Source

AskStatus = Literal["answered", "no_answer", "needs_info", "needs_review"]


class AskIn(BaseModel):
    token: str = Field(max_length=100)
    question: str = Field(max_length=5000)
    # Set when the visitor is replying to a "need more info" answer: the question they were answering.
    previous_question: str | None = Field(default=None, max_length=5000)


class QuestionTypeOut(BaseModel):
    label: str
    confidence: float
    method: str


class AskOut(BaseModel):
    status: AskStatus
    answer: str
    resolved_question: str  # what was actually answered (includes the earlier question for follow-ups)
    question_type: QuestionTypeOut | None
    verdict: Verdict | None
    decisions: list[DecisionResult]
    sources: list[Source]
    notices: list[str]
    timings_ms: dict[str, float]


class PublicAssistantOut(BaseModel):
    organization_name: str
    ready: bool
    suggested_questions: list[str] = Field(default_factory=list)

from datetime import datetime

from pydantic import BaseModel


class RecentQuestion(BaseModel):
    question: str
    status: str
    question_type: str | None
    verdict: str | None
    latency_ms: int
    created_at: datetime


class UsageOut(BaseModel):
    total_questions: int
    answered: int
    no_answer: int
    needs_info: int
    needs_review: int
    by_question_type: dict[str, int]
    avg_latency_ms: int
    recent: list[RecentQuestion]

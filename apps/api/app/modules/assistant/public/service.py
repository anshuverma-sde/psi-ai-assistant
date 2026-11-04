"""Application logic around the reasoning graph: tenant resolution, validation, logging."""

import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container
from app.core.errors import AppError, ErrorCode
from app.core.middleware.request_id import get_request_id
from app.modules.analytics.service import AnalyticsService
from app.modules.assistant.public.schemas import AskOut, QuestionTypeOut
from app.modules.assistant.token.service import AssistantContext, AssistantTokenService
from app.modules.knowledge_base.documents.repository import DocumentRepository
from app.modules.reasoning.generation.citation_validator import build_sources
from app.modules.reasoning.generation.templates import KB_EMPTY

logger = logging.getLogger(__name__)

FOLLOW_UP_JOINER = " Additional details: "


class AskService:
    def __init__(self, db: AsyncSession, container: Container) -> None:
        self.db = db
        self.c = container

    def _validate_question(self, question: str) -> str:
        question = " ".join(question.split())
        if not question:
            raise AppError(ErrorCode.QUESTION_EMPTY, field="question")
        limit = self.c.settings.max_question_chars
        if len(question) > limit:
            raise AppError(ErrorCode.QUESTION_TOO_LONG,
                           f"Please keep your question under {limit} characters.", field="question",
                           details={"max_chars": limit})
        return question

    def _with_previous(self, question: str, previous_question: str | None) -> str:
        """A reply to "I need more details" is answered together with the question it belongs to."""
        previous = " ".join((previous_question or "").split())
        if not previous:
            return question
        # Keep the original question intact; cap the total so repeated follow-ups can't grow forever.
        previous = previous[: self.c.settings.max_question_chars * 3]
        return f"{previous}{FOLLOW_UP_JOINER}{question}"

    async def ask(self, token: str, raw_question: str, previous_question: str | None = None) -> AskOut:
        started = time.perf_counter()
        # 1. Organization identification — from the token, server-side, never from the client.
        assistant: AssistantContext = await AssistantTokenService(self.db).resolve(token)
        question = self._with_previous(self._validate_question(raw_question), previous_question)

        if await DocumentRepository(self.db).count_ready(assistant.org_id) == 0:
            out = AskOut(status="no_answer", answer=KB_EMPTY.format(org=assistant.org_name), resolved_question=question,
                         question_type=None, verdict=None, decisions=[], sources=[],
                         notices=["knowledge_base_empty"], timings_ms={})
            await self._log(assistant, question, out, started)
            return out

        # 2–8. Classify → retrieve → gate → decompose → decide (parallel) → combine → generate.
        state = await self.c.ask_graph.run(org_id=assistant.org_id, org_name=assistant.org_name,
                                           question=question)

        classification = state.get("classification")
        out = AskOut(
            status=state["status"],
            answer=state["answer"],
            resolved_question=question,
            question_type=QuestionTypeOut(label=classification.label, confidence=classification.confidence,
                                          method=classification.method) if classification else None,
            verdict=state.get("verdict"),
            decisions=sorted(state.get("decision_results", []), key=lambda r: r.id),
            sources=build_sources(state.get("cited", []), state["context"]) if state.get("context") else [],
            notices=list(dict.fromkeys(state.get("notices", []))),
            timings_ms=state.get("timings", {}),
        )
        await self._log(assistant, question, out, started)
        return out

    async def _log(self, assistant: AssistantContext, question: str, out: AskOut, started: float) -> None:
        try:
            await AnalyticsService(self.db).log_query(
                org_id=assistant.org_id,
                request_id=get_request_id(),
                question=question,
                out=out,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception:  # analytics must never break answering
            logger.exception("Failed to log query")
            await self.db.rollback()

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import QueryLog
from app.modules.analytics.schemas import RecentQuestion, UsageOut

if TYPE_CHECKING:
    from app.modules.assistant.public.schemas import AskOut


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log_query(self, *, org_id: uuid.UUID, request_id: str | None, question: str,
                        out: "AskOut", latency_ms: int) -> None:
        self.db.add(QueryLog(
            org_id=org_id,
            request_id=request_id,
            question=question[:2000],
            question_type=out.question_type.label if out.question_type else None,
            type_confidence=out.question_type.confidence if out.question_type else None,
            status=out.status,
            verdict=out.verdict.outcome if out.verdict else None,
            decisions=[d.model_dump(mode="json") for d in out.decisions],
            sources=[s.model_dump(mode="json") for s in out.sources],
            step_timings=out.timings_ms,
            notices=out.notices,
            latency_ms=latency_ms,
        ))
        await self.db.commit()

    async def usage(self, org_id: uuid.UUID) -> UsageOut:
        by_status = dict((await self.db.execute(
            select(QueryLog.status, func.count()).where(QueryLog.org_id == org_id).group_by(QueryLog.status)
        )).all())
        by_type = dict((await self.db.execute(
            select(QueryLog.question_type, func.count())
            .where(QueryLog.org_id == org_id, QueryLog.question_type.is_not(None))
            .group_by(QueryLog.question_type)
        )).all())
        avg_latency = await self.db.scalar(
            select(func.avg(QueryLog.latency_ms)).where(QueryLog.org_id == org_id)
        )
        recent_rows = await self.db.scalars(
            select(QueryLog).where(QueryLog.org_id == org_id).order_by(QueryLog.created_at.desc()).limit(10)
        )
        return UsageOut(
            total_questions=sum(by_status.values()),
            answered=by_status.get("answered", 0),
            no_answer=by_status.get("no_answer", 0),
            needs_info=by_status.get("needs_info", 0),
            needs_review=by_status.get("needs_review", 0),
            by_question_type=by_type,
            avg_latency_ms=int(avg_latency or 0),
            recent=[RecentQuestion(question=r.question, status=r.status, question_type=r.question_type,
                                   verdict=r.verdict, latency_ms=r.latency_ms, created_at=r.created_at)
                    for r in recent_rows],
        )

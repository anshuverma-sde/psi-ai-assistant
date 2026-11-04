import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, CreatedAt, UUIDPrimaryKey


class QueryLog(UUIDPrimaryKey, CreatedAt, Base):
    """One row per visitor question — powers usage stats and debugging."""

    __tablename__ = "query_logs"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    request_id: Mapped[str | None] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str | None] = mapped_column(String(32))
    type_confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    verdict: Mapped[str | None] = mapped_column(String(32))
    decisions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    step_timings: Mapped[dict[str, float] | None] = mapped_column(JSONB)
    notices: Mapped[list[str] | None] = mapped_column(JSONB)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

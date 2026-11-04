import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.core.security.tokens import generate_assistant_token, looks_like_assistant_token
from app.modules.assistant.models import Assistant
from app.modules.organization.models import Organization


@dataclass(frozen=True)
class AssistantContext:
    """Who a public request is talking to — resolved server-side from the token only."""

    assistant_id: uuid.UUID
    org_id: uuid.UUID
    org_name: str


class AssistantTokenService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_for_org(self, org_id: uuid.UUID) -> Assistant:
        assistant = Assistant(org_id=org_id, public_token=generate_assistant_token())
        self.db.add(assistant)
        await self.db.flush()
        return assistant

    async def get_for_org(self, org_id: uuid.UUID) -> Assistant:
        assistant = await self.db.scalar(select(Assistant).where(Assistant.org_id == org_id))
        if assistant is None:
            raise AppError(ErrorCode.NOT_FOUND, "Assistant not found.")
        return assistant

    async def regenerate(self, org_id: uuid.UUID) -> Assistant:
        """Rotates the token; the previous URL/embed code stops working immediately."""
        assistant = await self.get_for_org(org_id)
        assistant.public_token = generate_assistant_token()
        assistant.rotated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return assistant

    async def resolve(self, token: str) -> AssistantContext:
        if not looks_like_assistant_token(token):
            raise AppError(ErrorCode.TOKEN_INVALID)
        row = (
            await self.db.execute(
                select(Assistant.id, Assistant.org_id, Organization.name)
                .join(Organization, Organization.id == Assistant.org_id)
                .where(Assistant.public_token == token, Assistant.is_active.is_(True))
            )
        ).first()
        if row is None:
            raise AppError(ErrorCode.TOKEN_INVALID)
        return AssistantContext(assistant_id=row[0], org_id=row[1], org_name=row[2])

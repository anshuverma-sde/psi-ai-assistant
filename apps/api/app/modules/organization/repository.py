import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.models import Organization


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, name: str) -> Organization:
        org = Organization(name=name)
        self.db.add(org)
        await self.db.flush()
        return org

    async def get(self, org_id: uuid.UUID) -> Organization | None:
        return await self.db.get(Organization, org_id)

    async def lock(self, org_id: uuid.UUID) -> Organization | None:
        """Row lock used to serialize per-org limit checks (e.g. document count)."""
        return await self.db.scalar(
            select(Organization).where(Organization.id == org_id).with_for_update()
        )

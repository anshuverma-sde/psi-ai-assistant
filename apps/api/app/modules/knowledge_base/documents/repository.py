"""Every query is scoped by org_id — there is no way to fetch a document without it."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.documents.models import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_org(self, org_id: uuid.UUID) -> list[Document]:
        result = await self.db.scalars(
            select(Document).where(Document.org_id == org_id).order_by(Document.created_at.desc())
        )
        return list(result)

    async def get(self, org_id: uuid.UUID, document_id: uuid.UUID) -> Document | None:
        return await self.db.scalar(
            select(Document).where(Document.id == document_id, Document.org_id == org_id)
        )

    async def count(self, org_id: uuid.UUID) -> int:
        return await self.db.scalar(select(func.count()).where(Document.org_id == org_id)) or 0

    async def count_ready(self, org_id: uuid.UUID) -> int:
        return await self.db.scalar(
            select(func.count()).where(Document.org_id == org_id, Document.status == DocumentStatus.READY)
        ) or 0

    async def ready_names(self, org_id: uuid.UUID, limit: int = 3) -> list[str]:
        result = await self.db.scalars(
            select(Document.original_name)
            .where(Document.org_id == org_id, Document.status == DocumentStatus.READY)
            .order_by(Document.created_at)
            .limit(limit)
        )
        return list(result)

    async def find_by_checksum(self, org_id: uuid.UUID, checksum: str) -> Document | None:
        return await self.db.scalar(
            select(Document).where(Document.org_id == org_id, Document.checksum == checksum)
        )

    def add(self, document: Document) -> None:
        self.db.add(document)

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)

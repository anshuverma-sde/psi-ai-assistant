import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container
from app.core.errors import AppError, ErrorCode
from app.modules.knowledge_base.documents.models import Document, DocumentStatus
from app.modules.knowledge_base.documents.repository import DocumentRepository
from app.modules.knowledge_base.documents.schemas import DocumentListOut, DocumentOut, KnowledgeBaseLimits
from app.modules.knowledge_base.documents.validators import ValidatedPdf, read_upload, validate_pdf
from app.modules.knowledge_base.ingestion.indexer import delete_document_vectors
from app.modules.organization.repository import OrganizationRepository

logger = logging.getLogger(__name__)


def _storage_key(org_id: uuid.UUID, document_id: uuid.UUID, checksum: str) -> str:
    return f"{org_id}/{document_id}-{checksum[:12]}.pdf"


class DocumentService:
    def __init__(self, db: AsyncSession, container: Container) -> None:
        self.db = db
        self.c = container
        self.settings = container.settings
        self.repo = DocumentRepository(db)
        self.orgs = OrganizationRepository(db)

    # ---- queries -------------------------------------------------------------------------------
    async def list(self, org_id: uuid.UUID) -> DocumentListOut:
        docs = await self.repo.list_for_org(org_id)
        return DocumentListOut(
            documents=[DocumentOut.model_validate(d) for d in docs],
            limits=self.limits(len(docs)),
        )

    def limits(self, used: int) -> KnowledgeBaseLimits:
        s = self.settings
        return KnowledgeBaseLimits(
            max_documents=s.max_documents, max_pages=s.max_pages, max_file_mb=s.max_file_mb,
            used_documents=used, remaining_documents=max(0, s.max_documents - used),
        )

    async def get(self, org_id: uuid.UUID, document_id: uuid.UUID) -> Document:
        doc = await self.repo.get(org_id, document_id)
        if doc is None:  # 404 for other orgs' ids too — no existence leak
            raise AppError(ErrorCode.NOT_FOUND, "Document not found.")
        return doc

    # ---- commands ------------------------------------------------------------------------------
    async def _read_and_validate(self, file: UploadFile) -> ValidatedPdf:
        s = self.settings
        data = await read_upload(file, s.max_file_bytes, s.max_file_mb)
        return await validate_pdf(data, file.filename, s.max_pages)

    async def _ensure_not_duplicate(self, org_id: uuid.UUID, pdf: ValidatedPdf,
                                    exclude_id: uuid.UUID | None = None) -> None:
        existing = await self.repo.find_by_checksum(org_id, pdf.checksum)
        if existing and existing.id != exclude_id:
            raise AppError(
                ErrorCode.DOC_DUPLICATE,
                f"This file is already in your knowledge base as “{existing.original_name}”.",
                field="file",
            )

    def _limit_error(self) -> AppError:
        return AppError(
            ErrorCode.DOC_LIMIT_REACHED,
            f"You can upload at most {self.settings.max_documents} documents. "
            "Delete or replace an existing document first.",
            details={"max_documents": self.settings.max_documents},
        )

    async def upload(self, org_id: uuid.UUID, file: UploadFile) -> Document:
        # Cheap pre-check so we don't read 10 MB just to reject it.
        if await self.repo.count(org_id) >= self.settings.max_documents:
            raise self._limit_error()

        pdf = await self._read_and_validate(file)

        # Authoritative check under a row lock: concurrent uploads can't exceed the limit.
        await self.orgs.lock(org_id)
        if await self.repo.count(org_id) >= self.settings.max_documents:
            raise self._limit_error()
        await self._ensure_not_duplicate(org_id, pdf)

        doc = Document(
            id=uuid.uuid4(), org_id=org_id, original_name=pdf.filename, size_bytes=pdf.size_bytes,
            page_count=pdf.page_count, checksum=pdf.checksum, status=DocumentStatus.PENDING,
        )
        doc.storage_key = _storage_key(org_id, doc.id, pdf.checksum)
        await self.c.storage.save(doc.storage_key, pdf.data)
        self.repo.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def replace(self, org_id: uuid.UUID, document_id: uuid.UUID, file: UploadFile) -> Document:
        doc = await self.get(org_id, document_id)
        pdf = await self._read_and_validate(file)
        await self._ensure_not_duplicate(org_id, pdf, exclude_id=doc.id)

        old_key = doc.storage_key
        new_key = _storage_key(org_id, doc.id, pdf.checksum)
        await self.c.storage.save(new_key, pdf.data)
        await delete_document_vectors(self.c.vector_store, doc.id)

        doc.original_name = pdf.filename
        doc.size_bytes = pdf.size_bytes
        doc.page_count = pdf.page_count
        doc.checksum = pdf.checksum
        doc.storage_key = new_key
        doc.status = DocumentStatus.PENDING
        doc.chunk_count = 0
        doc.error_code = doc.error_message = None
        await self.db.commit()
        await self.db.refresh(doc)
        if old_key != new_key:
            await self.c.storage.delete(old_key)
        return doc

    async def delete(self, org_id: uuid.UUID, document_id: uuid.UUID) -> None:
        doc = await self.get(org_id, document_id)
        await delete_document_vectors(self.c.vector_store, doc.id)
        await self.repo.delete(doc)
        await self.db.commit()
        await self.c.storage.delete(doc.storage_key)

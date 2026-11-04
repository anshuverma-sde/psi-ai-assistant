"""Background pipeline: stored PDF → pages → chunks → embeddings → vector store."""

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

from app.core.errors import AppError, ErrorCode
from app.modules.knowledge_base.documents.models import Document, DocumentStatus
from app.modules.knowledge_base.ingestion.chunker import PageAwareChunker
from app.modules.knowledge_base.ingestion.extractor import extract_pages
from app.modules.knowledge_base.ingestion.indexer import build_nodes, delete_document_vectors, index_nodes

if TYPE_CHECKING:
    from app.container import Container

logger = logging.getLogger(__name__)

_MIN_TEXT_CHARS = 40


class IngestionService:
    def __init__(self, container: "Container") -> None:
        self.c = container
        self.chunker = PageAwareChunker(container.settings.chunk_size, container.settings.chunk_overlap)

    async def process(self, document_id: uuid.UUID, checksum: str) -> None:
        """Never raises: failures are recorded on the document row for the dashboard."""
        try:
            doc = await self._set_status(document_id, checksum, DocumentStatus.PROCESSING)
            if doc is None:
                return
            chunk_count = await self._ingest(doc)
            await self._set_status(document_id, checksum, DocumentStatus.READY, chunk_count=chunk_count)
            logger.info("Indexed %s (%s chunks)", doc.original_name, chunk_count)
        except AppError as exc:
            logger.warning("Ingestion rejected %s: %s", document_id, exc.message)
            await self._fail(document_id, checksum, exc.code, exc.message)
        except Exception:
            logger.exception("Ingestion failed for %s", document_id)
            await self._fail(document_id, checksum, ErrorCode.PROCESSING_FAILED,
                             "The document could not be processed. Try re-uploading it.")

    async def _ingest(self, doc: Document) -> int:
        data = await self.c.storage.read(doc.storage_key)
        pages = await asyncio.to_thread(extract_pages, data)
        if sum(len(p.text) for p in pages) < _MIN_TEXT_CHARS:
            raise AppError(ErrorCode.PDF_NO_TEXT)

        drafts = self.chunker.chunk(pages)
        nodes = await build_nodes(drafts, self.c.embeddings, org_id=doc.org_id,
                                  document_id=doc.id, filename=doc.original_name)
        # Idempotent: clear anything from a previous attempt before writing.
        await delete_document_vectors(self.c.vector_store, doc.id)
        await index_nodes(self.c.vector_store, nodes)
        return len(nodes)

    async def _set_status(self, document_id: uuid.UUID, checksum: str, status: DocumentStatus,
                          *, chunk_count: int | None = None) -> Document | None:
        async with self.c.db.session_factory() as db:
            doc = await db.get(Document, document_id)
            # Skip if deleted or replaced by a newer upload while we were working.
            if doc is None or doc.checksum != checksum:
                if status == DocumentStatus.READY:
                    await delete_document_vectors(self.c.vector_store, document_id)
                return None
            doc.status = status
            if chunk_count is not None:
                doc.chunk_count = chunk_count
            doc.error_code = doc.error_message = None
            await db.commit()
            await db.refresh(doc)
            return doc

    async def _fail(self, document_id: uuid.UUID, checksum: str, code: ErrorCode, message: str) -> None:
        async with self.c.db.session_factory() as db:
            doc = await db.get(Document, document_id)
            if doc is None or doc.checksum != checksum:
                return
            doc.status = DocumentStatus.FAILED
            doc.error_code = code.value
            doc.error_message = message[:500]
            await db.commit()
        await delete_document_vectors(self.c.vector_store, document_id)

    async def resume_pending(self) -> None:
        """On startup, re-run documents left PENDING/PROCESSING by a restart."""
        from sqlalchemy import select

        async with self.c.db.session_factory() as db:
            rows = (await db.execute(
                select(Document.id, Document.checksum).where(
                    Document.status.in_([DocumentStatus.PENDING, DocumentStatus.PROCESSING]))
            )).all()
        for doc_id, checksum in rows:
            await self.process(doc_id, checksum)

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.knowledge_base.documents.models import DocumentStatus


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_name: str
    size_bytes: int
    page_count: int
    status: DocumentStatus
    chunk_count: int
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseLimits(BaseModel):
    max_documents: int
    max_pages: int
    max_file_mb: int
    used_documents: int
    remaining_documents: int


class DocumentListOut(BaseModel):
    documents: list[DocumentOut]
    limits: KnowledgeBaseLimits

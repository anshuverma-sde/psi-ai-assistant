import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.container import Container
from app.core.deps import CurrentAuth, DbSession, get_container
from app.core.responses import ApiResponse, Deleted, deleted, ok
from app.modules.knowledge_base.documents.schemas import DocumentListOut, DocumentOut
from app.modules.knowledge_base.documents.service import DocumentService
from app.modules.knowledge_base.ingestion.service import IngestionService

router = APIRouter(prefix="/api/admin/documents", tags=["knowledge base (admin)"])

ContainerDep = Annotated[Container, Depends(get_container)]
PdfFile = Annotated[UploadFile, File(description="PDF document (max 10 MB, 20 pages)")]


@router.get("", response_model=ApiResponse[DocumentListOut])
async def list_documents(auth: CurrentAuth, db: DbSession, c: ContainerDep):
    return ok(await DocumentService(db, c).list(auth.org_id))


@router.get("/{document_id}", response_model=ApiResponse[DocumentOut])
async def get_document(document_id: uuid.UUID, auth: CurrentAuth, db: DbSession, c: ContainerDep):
    return ok(DocumentOut.model_validate(await DocumentService(db, c).get(auth.org_id, document_id)))


@router.post("", response_model=ApiResponse[DocumentOut], status_code=201)
async def upload_document(file: PdfFile, tasks: BackgroundTasks, auth: CurrentAuth,
                          db: DbSession, c: ContainerDep):
    doc = await DocumentService(db, c).upload(auth.org_id, file)
    tasks.add_task(IngestionService(c).process, doc.id, doc.checksum)
    return ok(DocumentOut.model_validate(doc))


@router.put("/{document_id}", response_model=ApiResponse[DocumentOut])
async def replace_document(document_id: uuid.UUID, file: PdfFile, tasks: BackgroundTasks,
                           auth: CurrentAuth, db: DbSession, c: ContainerDep):
    doc = await DocumentService(db, c).replace(auth.org_id, document_id, file)
    tasks.add_task(IngestionService(c).process, doc.id, doc.checksum)
    return ok(DocumentOut.model_validate(doc))


@router.delete("/{document_id}", response_model=ApiResponse[Deleted])
async def delete_document(document_id: uuid.UUID, auth: CurrentAuth, db: DbSession, c: ContainerDep):
    await DocumentService(db, c).delete(auth.org_id, document_id)
    return deleted(document_id)

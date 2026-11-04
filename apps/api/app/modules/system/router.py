from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.responses import ApiResponse, ok

router = APIRouter(tags=["system"])


class HealthOut(BaseModel):
    status: str
    database: bool


class LimitsOut(BaseModel):
    max_documents: int
    max_pages: int
    max_file_mb: int
    max_question_chars: int


@router.get("/api/health", response_model=ApiResponse[HealthOut])
async def health(db: DbSession):
    await db.execute(text("SELECT 1"))
    return ok(HealthOut(status="ok", database=True))


@router.get("/api/meta/limits", response_model=ApiResponse[LimitsOut])
async def limits():
    s = get_settings()
    return ok(LimitsOut(max_documents=s.max_documents, max_pages=s.max_pages,
                        max_file_mb=s.max_file_mb, max_question_chars=s.max_question_chars))

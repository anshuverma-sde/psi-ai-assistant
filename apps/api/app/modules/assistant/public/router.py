from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.container import Container
from app.core.config import get_settings
from app.core.deps import DbSession, get_container
from app.core.rate_limit import limiter
from app.core.responses import ApiResponse, ok
from app.modules.assistant.public.schemas import AskIn, AskOut, PublicAssistantOut
from app.modules.assistant.public.service import AskService
from app.modules.assistant.token.service import AssistantTokenService
from app.modules.knowledge_base.documents.repository import DocumentRepository

router = APIRouter(tags=["assistant (public)"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.post("/api/ask", response_model=ApiResponse[AskOut])
@limiter.limit(lambda: get_settings().ask_rate_limit)
async def ask(request: Request, payload: AskIn, db: DbSession, c: ContainerDep):
    """Public endpoint used by the chat widget. Authenticated only by the assistant token."""
    return ok(await AskService(db, c).ask(payload.token, payload.question, payload.previous_question))


@router.get("/api/public/assistant/{token}", response_model=ApiResponse[PublicAssistantOut])
async def public_assistant(token: str, db: DbSession):
    """Minimal public info for the chat header. Never exposes documents."""
    assistant = await AssistantTokenService(db).resolve(token)
    names = await DocumentRepository(db).ready_names(assistant.org_id)
    return ok(PublicAssistantOut(organization_name=assistant.org_name, ready=bool(names),
                                 suggested_questions=suggested_questions(names)))


def suggested_questions(document_names: list[str]) -> list[str]:
    """Conversation starters derived from document titles (titles only — never content)."""
    titles = [n.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip() for n in document_names]
    return [f"What does the {t} document cover?" for t in titles if t]

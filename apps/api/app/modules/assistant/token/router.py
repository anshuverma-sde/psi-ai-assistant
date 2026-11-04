from fastapi import APIRouter

from app.core.config import get_settings
from app.core.deps import CurrentAuth, DbSession
from app.core.responses import ApiResponse, ok
from app.modules.assistant.embed.service import build_assistant_out
from app.modules.assistant.schemas import AssistantOut
from app.modules.assistant.token.service import AssistantTokenService

router = APIRouter(prefix="/api/admin/assistant", tags=["assistant (admin)"])


@router.get("", response_model=ApiResponse[AssistantOut])
async def get_assistant(auth: CurrentAuth, db: DbSession):
    assistant = await AssistantTokenService(db).get_for_org(auth.org_id)
    return ok(build_assistant_out(assistant, get_settings().public_app_url))


@router.post("/regenerate", response_model=ApiResponse[AssistantOut])
async def regenerate_token(auth: CurrentAuth, db: DbSession):
    assistant = await AssistantTokenService(db).regenerate(auth.org_id)
    return ok(build_assistant_out(assistant, get_settings().public_app_url))

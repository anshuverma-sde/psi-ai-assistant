from fastapi import APIRouter, Response

from app.core.config import get_settings
from app.core.deps import CurrentAuth, DbSession
from app.core.responses import ApiResponse, ok
from app.core.security.jwt import create_session_token
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginIn, RegisterIn, SessionOut
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user.id, user.org_id),
        max_age=settings.jwt_expires_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/register", response_model=ApiResponse[SessionOut], status_code=201)
async def register(data: RegisterIn, response: Response, db: DbSession):
    user, session = await AuthService(db).register(data)
    _set_session_cookie(response, user)
    return ok(session)


@router.post("/login", response_model=ApiResponse[SessionOut])
async def login(data: LoginIn, response: Response, db: DbSession):
    user, session = await AuthService(db).login(data)
    _set_session_cookie(response, user)
    return ok(session)


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(response: Response):
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    return ok({"logged_out": True})


@router.get("/me", response_model=ApiResponse[SessionOut])
async def me(auth: CurrentAuth, db: DbSession):
    return ok(await AuthService(db).session_for(auth.user_id, auth.org_id))

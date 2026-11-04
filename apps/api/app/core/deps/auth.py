"""Admin authentication. The org id ONLY ever comes from a verified session token."""

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps.db import DbSession
from app.core.errors import AppError, ErrorCode
from app.core.security.jwt import decode_session_token


@dataclass(frozen=True)
class AuthContext:
    user_id: uuid.UUID
    org_id: uuid.UUID
    email: str


def _extract_token(request: Request) -> str | None:
    cookie = request.cookies.get(get_settings().session_cookie_name)
    if cookie:
        return cookie
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


async def get_auth_context(request: Request, db: DbSession) -> AuthContext:
    from app.modules.auth.models import User  # local import keeps core free of module imports at load

    token = _extract_token(request)
    claims = decode_session_token(token) if token else None
    if claims is None:
        raise AppError(ErrorCode.UNAUTHORIZED)

    user = await db.scalar(select(User).where(User.id == claims.user_id, User.org_id == claims.org_id))
    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED)
    return AuthContext(user_id=user.id, org_id=user.org_id, email=user.email)


CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]

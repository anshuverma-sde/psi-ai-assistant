from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import get_settings

_ALGORITHM = "HS256"
_AUDIENCE = "psi-admin"


@dataclass(frozen=True)
class SessionClaims:
    user_id: UUID
    org_id: UUID


def create_session_token(user_id: UUID, org_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "org": str(org_id),
        "aud": _AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_session_token(token: str) -> SessionClaims | None:
    """Returns claims for a valid admin session token, otherwise None."""
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret, algorithms=[_ALGORITHM], audience=_AUDIENCE
        )
        return SessionClaims(user_id=UUID(payload["sub"]), org_id=UUID(payload["org"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None

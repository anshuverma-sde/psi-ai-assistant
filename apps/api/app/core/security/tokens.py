import re
import secrets

ASSISTANT_TOKEN_PREFIX = "ast_"
_TOKEN_SHAPE = re.compile(r"^ast_[A-Za-z0-9_\-]{40,64}$")


def generate_assistant_token() -> str:
    """Random, unguessable, URL-safe publishable key (256 bits of entropy)."""
    return ASSISTANT_TOKEN_PREFIX + secrets.token_urlsafe(32)


def looks_like_assistant_token(value: str) -> bool:
    """Cheap shape check so garbage never reaches the database."""
    return bool(_TOKEN_SHAPE.match(value or ""))

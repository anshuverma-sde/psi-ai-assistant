from slowapi import Limiter
from starlette.requests import Request


def client_key(request: Request) -> str:
    """Client IP; honours X-Forwarded-For set by the Next.js proxy in front of the API."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "anonymous"


limiter = Limiter(key_func=client_key, headers_enabled=False)

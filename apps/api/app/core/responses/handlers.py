"""Turns every failure into the standard error envelope."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors.codes import ErrorCode
from app.core.errors.exceptions import AppError
from app.core.responses.builders import fail

logger = logging.getLogger(__name__)

_HTTP_STATUS_TO_CODE = {
    401: ErrorCode.UNAUTHORIZED,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.NOT_FOUND,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMITED,
}


async def app_error_handler(_: Request, exc: AppError):
    return fail(exc.code, exc.message, details=exc.details, field=exc.field, status_code=exc.status_code)


async def validation_error_handler(_: Request, exc: RequestValidationError):
    fields: dict[str, str] = {}
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path", "form")]
        fields[".".join(loc) or "request"] = err.get("msg", "Invalid value").removeprefix("Value error, ")
    first_field = next(iter(fields), None)
    message = fields[first_field] if len(fields) == 1 and first_field else None
    return fail(ErrorCode.VALIDATION_ERROR, message, details={"fields": fields}, field=first_field)


async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    code = _HTTP_STATUS_TO_CODE.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    message = exc.detail if isinstance(exc.detail, str) and exc.status_code < 500 else None
    return fail(code, message, status_code=exc.status_code)


async def rate_limit_handler(_: Request, exc: RateLimitExceeded):
    return fail(ErrorCode.RATE_LIMITED, details={"limit": str(exc.detail)})


async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return fail(ErrorCode.INTERNAL_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

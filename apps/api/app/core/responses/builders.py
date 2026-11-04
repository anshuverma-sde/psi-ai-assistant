"""Helpers routers use to build responses. Routers never hand-build dicts."""

import math
from datetime import datetime, timezone
from typing import Any, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.errors.codes import ErrorCode, default_message_for, http_status_for
from app.core.middleware.request_id import get_request_id
from app.core.responses.envelope import ApiResponse, Deleted, ErrorBody, Meta, PaginationMeta

T = TypeVar("T")


def build_meta(pagination: PaginationMeta | None = None) -> Meta:
    return Meta(
        request_id=get_request_id(),
        timestamp=datetime.now(timezone.utc),
        pagination=pagination,
    )


def ok(data: T) -> ApiResponse[T]:
    """200/201 success. The status code comes from the route decorator."""
    return ApiResponse[Any](success=True, data=data, error=None, meta=build_meta())


created = ok


def deleted(resource_id: Any) -> ApiResponse[Deleted]:
    return ok(Deleted(id=str(resource_id)))


def paginated(items: list[T], *, page: int, size: int, total: int) -> ApiResponse[list[T]]:
    pagination = PaginationMeta(
        page=page, size=size, total=total, pages=math.ceil(total / size) if size else 0
    )
    return ApiResponse[Any](success=True, data=items, error=None, meta=build_meta(pagination))


def fail(
    code: ErrorCode,
    message: str | None = None,
    *,
    details: dict[str, Any] | None = None,
    field: str | None = None,
    status_code: int | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ApiResponse[None](
        success=False,
        data=None,
        error=ErrorBody(
            code=code.value,
            message=message or default_message_for(code),
            details=details,
            field=field,
        ),
        meta=build_meta(),
    )
    return JSONResponse(
        status_code=status_code or http_status_for(code),
        content=jsonable_encoder(body),
        headers=headers,
    )

"""The response envelope every endpoint returns — success or failure."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    field: str | None = None


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int
    pages: int


class Meta(BaseModel):
    request_id: str | None = None
    timestamp: datetime
    pagination: PaginationMeta | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorBody | None = None
    meta: Meta


class Deleted(BaseModel):
    id: str
    deleted: bool = Field(default=True)

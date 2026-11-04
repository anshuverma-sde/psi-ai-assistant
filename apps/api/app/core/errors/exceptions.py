from typing import Any

from app.core.errors.codes import ErrorCode, default_message_for, http_status_for


class AppError(Exception):
    """The only exception type business code raises.

    Converted into the standard error envelope by `core.responses.handlers`.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        field: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.code = code
        self.message = message or default_message_for(code)
        self.details = details
        self.field = field
        self.status_code = status_code or http_status_for(code)
        super().__init__(self.message)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"AppError({self.code.value}, {self.message!r})"

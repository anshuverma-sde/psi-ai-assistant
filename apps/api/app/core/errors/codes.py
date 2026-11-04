"""Single source of truth for every error the API can return."""

from enum import Enum


class ErrorCode(str, Enum):
    # Generic
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    # Auth
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    # Documents
    PDF_INVALID = "PDF_INVALID"
    PDF_ENCRYPTED = "PDF_ENCRYPTED"
    PDF_TOO_LARGE = "PDF_TOO_LARGE"
    PDF_TOO_MANY_PAGES = "PDF_TOO_MANY_PAGES"
    PDF_EMPTY = "PDF_EMPTY"
    PDF_NO_TEXT = "PDF_NO_TEXT"
    DOC_LIMIT_REACHED = "DOC_LIMIT_REACHED"
    DOC_DUPLICATE = "DOC_DUPLICATE"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    # Assistant
    TOKEN_INVALID = "TOKEN_INVALID"
    QUESTION_EMPTY = "QUESTION_EMPTY"
    QUESTION_TOO_LONG = "QUESTION_TOO_LONG"
    # AI
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    DECISION_FAILED = "DECISION_FAILED"


# code -> (http status, default user-facing message)
ERROR_CATALOG: dict[ErrorCode, tuple[int, str]] = {
    ErrorCode.VALIDATION_ERROR: (422, "Some fields are invalid."),
    ErrorCode.NOT_FOUND: (404, "The requested resource was not found."),
    ErrorCode.RATE_LIMITED: (429, "Too many requests. Please wait a moment and try again."),
    ErrorCode.INTERNAL_ERROR: (500, "Something went wrong on our side. Please try again."),
    ErrorCode.UNAUTHORIZED: (401, "Please log in to continue."),
    ErrorCode.INVALID_CREDENTIALS: (401, "Incorrect email or password."),
    ErrorCode.EMAIL_TAKEN: (409, "An account with this email already exists."),
    ErrorCode.PDF_INVALID: (400, "This file is not a valid PDF document."),
    ErrorCode.PDF_ENCRYPTED: (400, "Password-protected PDFs are not supported."),
    ErrorCode.PDF_TOO_LARGE: (413, "The PDF is larger than the allowed maximum size."),
    ErrorCode.PDF_TOO_MANY_PAGES: (400, "The PDF has more pages than allowed."),
    ErrorCode.PDF_EMPTY: (400, "The uploaded file is empty."),
    ErrorCode.PDF_NO_TEXT: (
        422,
        "No readable text was found in this PDF. Scanned/image-only PDFs are not supported.",
    ),
    ErrorCode.DOC_LIMIT_REACHED: (
        409,
        "Document limit reached. Delete or replace an existing document first.",
    ),
    ErrorCode.DOC_DUPLICATE: (409, "This document has already been uploaded."),
    ErrorCode.PROCESSING_FAILED: (500, "The document could not be processed."),
    ErrorCode.TOKEN_INVALID: (401, "This assistant link is invalid or has been regenerated."),
    ErrorCode.QUESTION_EMPTY: (400, "Please type a question."),
    ErrorCode.QUESTION_TOO_LONG: (400, "Your question is too long."),
    ErrorCode.LLM_UNAVAILABLE: (
        503,
        "The AI service is temporarily unavailable. Please try again shortly.",
    ),
    ErrorCode.DECISION_FAILED: (500, "The decision could not be evaluated."),
}


def http_status_for(code: ErrorCode) -> int:
    return ERROR_CATALOG[code][0]


def default_message_for(code: ErrorCode) -> str:
    return ERROR_CATALOG[code][1]

"""Upload validation: size, type, encryption and page limits — before any heavy processing."""

import asyncio
import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass

from fastapi import UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import AppError, ErrorCode

_READ_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class ValidatedPdf:
    data: bytes
    filename: str
    page_count: int
    checksum: str

    @property
    def size_bytes(self) -> int:
        return len(self.data)


def sanitize_filename(name: str | None) -> str:
    name = unicodedata.normalize("NFKC", (name or "document.pdf")).replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^\w.\- ()]+", "_", name).strip(" .") or "document.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name[-120:]


async def read_upload(file: UploadFile, max_bytes: int, max_mb: int) -> bytes:
    """Streams the upload and stops as soon as it exceeds the limit."""
    buf = bytearray()
    while chunk := await file.read(_READ_CHUNK):
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise AppError(
                ErrorCode.PDF_TOO_LARGE,
                f"“{sanitize_filename(file.filename)}” is larger than {max_mb} MB.",
                details={"max_mb": max_mb},
                field="file",
            )
    if not buf:
        raise AppError(ErrorCode.PDF_EMPTY, field="file")
    return bytes(buf)


def _inspect_pdf(data: bytes) -> int:
    if not data.lstrip()[:5].startswith(b"%PDF-"):
        raise AppError(ErrorCode.PDF_INVALID, field="file")
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted and not reader.decrypt(""):
            raise AppError(ErrorCode.PDF_ENCRYPTED, field="file")
        return len(reader.pages)
    except AppError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise AppError(ErrorCode.PDF_INVALID, details={"reason": str(exc)[:200]}, field="file") from exc
    except Exception as exc:  # pypdf can raise many internal errors on corrupt files
        raise AppError(ErrorCode.PDF_INVALID, field="file") from exc


async def validate_pdf(data: bytes, filename: str | None, max_pages: int) -> ValidatedPdf:
    clean_name = sanitize_filename(filename)
    page_count = await asyncio.to_thread(_inspect_pdf, data)
    if page_count == 0:
        raise AppError(ErrorCode.PDF_INVALID, "This PDF has no pages.", field="file")
    if page_count > max_pages:
        raise AppError(
            ErrorCode.PDF_TOO_MANY_PAGES,
            f"“{clean_name}” has {page_count} pages. The maximum is {max_pages}.",
            details={"pages": page_count, "max_pages": max_pages},
            field="file",
        )
    return ValidatedPdf(
        data=data,
        filename=clean_name,
        page_count=page_count,
        checksum=hashlib.sha256(data).hexdigest(),
    )

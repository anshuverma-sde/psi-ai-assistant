import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def make_pdf(pages: list[str] | None = None, *, n_pages: int | None = None, encrypt: str | None = None) -> bytes:
    """Builds a small text PDF in memory. `n_pages` repeats a filler page."""
    if pages is None:
        pages = [f"Filler page {i + 1}. Nothing interesting here." for i in range(n_pages or 1)]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, encrypt=encrypt)
    for text in pages:
        y = 800
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 16
        c.showPage()
    c.save()
    return buf.getvalue()


def make_blank_pdf(n_pages: int = 1) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for _ in range(n_pages):
        c.showPage()
    c.save()
    return buf.getvalue()

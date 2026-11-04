import io
import re
from dataclasses import dataclass

import pdfplumber

from app.modules.knowledge_base.ingestion.table_formatter import table_to_markdown


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-based, used in citations
    text: str


def _clean(text: str) -> str:
    text = text.replace(" ", " ")
    text = re.sub(r"\(cid:\d+\)\s*", "• ", text)  # unmapped glyphs (usually list bullets)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # de-hyphenate line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _outside(bboxes: list[tuple[float, float, float, float]]):
    def keep(obj: dict) -> bool:
        if "x0" not in obj or "top" not in obj:
            return True
        cx = (obj["x0"] + obj["x1"]) / 2
        cy = (obj["top"] + obj["bottom"]) / 2
        return not any(x0 <= cx <= x1 and top <= cy <= bottom for x0, top, x1, bottom in bboxes)

    return keep


def extract_pages(data: bytes) -> list[PageText]:
    """Per-page text; tables are pulled out separately and appended as markdown."""
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            tables = page.find_tables()
            bboxes = [t.bbox for t in tables]
            body = (page.filter(_outside(bboxes)) if bboxes else page).extract_text() or ""
            parts = [_clean(body)]
            for table in tables:
                md = table_to_markdown(table.extract())
                if md:
                    parts.append(f"Table:\n{md}")
            text = "\n\n".join(p for p in parts if p)
            if text:
                pages.append(PageText(page_number=index, text=text))
            page.close()
    return pages

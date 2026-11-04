"""Renders samples/source/<org>/*.md into samples/pdfs/<org>/*.pdf (reproducible test data).

Supported markdown subset: `#`/`##` headings, paragraphs, `-` bullets, `1.` numbered lists,
pipe tables (first row = header) and a `\\pagebreak` line.

Run:  apps/api/.venv/bin/python samples/scripts/generate_pdfs.py
"""

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE, OUTPUT = ROOT / "source", ROOT / "pdfs"

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=4,
                    textColor=colors.HexColor("#1e3a8a"))
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.5, leading=15)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=10, leading=13)


def inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def table(rows: list[list[str]]) -> Table:
    data = [[Paragraph(inline(c), CELL) for c in r] for r in rows]
    t = Table(data, hAlign="LEFT", colWidths=[170 / len(rows[0]) * mm] * len(rows[0]))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def render(md: str) -> list:
    flow, para, bullets, numbered, rows = [], [], [], [], []

    def flush():
        nonlocal para, bullets, numbered, rows
        if para:
            flow.append(Paragraph(inline(" ".join(para)), BODY))
            flow.append(Spacer(1, 4))
        if bullets:
            flow.append(ListFlowable([ListItem(Paragraph(inline(b), BODY)) for b in bullets],
                                     bulletType="bullet", leftIndent=14))
        if numbered:
            flow.append(ListFlowable([ListItem(Paragraph(inline(b), BODY)) for b in numbered],
                                     bulletType="1", leftIndent=14))
        if rows:
            flow.append(table(rows))
            flow.append(Spacer(1, 6))
        para, bullets, numbered, rows = [], [], [], []

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line == "\\pagebreak":
            flush()
            flow.append(PageBreak())
        elif line.startswith("## "):
            flush()
            flow.append(Paragraph(inline(line[3:]), H2))
        elif line.startswith("# "):
            flush()
            flow.append(Paragraph(inline(line[2:]), H1))
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append(cells)
        elif line.startswith("- "):
            bullets.append(line[2:])
        elif re.match(r"^\d+\.\s", line):
            numbered.append(re.sub(r"^\d+\.\s", "", line))
        else:
            para.append(line)
    flush()
    return flow


def footer(title: str):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(20 * mm, 12 * mm, title)
        canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return draw


def build(md_path: Path, pdf_path: Path) -> None:
    md = md_path.read_text(encoding="utf-8")
    title = md.splitlines()[0].lstrip("# ").strip()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, title=title, author="PSI sample data",
                            leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm)
    doc.build(render(md), onFirstPage=footer(title), onLaterPages=footer(title))


def main() -> int:
    count = 0
    for md_path in sorted(SOURCE.glob("*/*.md")):
        pdf_path = OUTPUT / md_path.parent.name / f"{md_path.stem}.pdf"
        build(md_path, pdf_path)
        count += 1
        print(f"  ✓ {pdf_path.relative_to(ROOT.parent)}")
    print(f"Generated {count} PDFs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

def _cell(value: object) -> str:
    return " ".join(str(value or "").split()).replace("|", "/")


def table_to_markdown(rows: list[list[object]]) -> str:
    """Renders an extracted table as markdown so thresholds/tiers stay row-aligned for the LLM."""
    rows = [[_cell(c) for c in row] for row in rows if row and any(c for c in row)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    header, *body = rows
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)

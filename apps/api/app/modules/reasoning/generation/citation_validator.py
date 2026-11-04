"""Keeps answers honest: only citations that point at retrieved excerpts survive."""

import re

from pydantic import BaseModel

from app.modules.reasoning.context import EvidenceContext

# Tolerates model variations like "[ s2 ]", "[S2]", "[s1, s3]" and full-width "【s1】".
_MARKER = re.compile(r"[\[【]\s*([sS]\d+(?:\s*,\s*[sS]\d+)*)\s*[\]】]")


class Source(BaseModel):
    id: str
    document_id: str
    document: str
    page: int
    snippet: str

    @property
    def reference(self) -> str:
        return f"{self.document} — Page {self.page}"


def clean_citations(answer: str, context: EvidenceContext) -> tuple[str, list[str]]:
    """Removes markers for unknown ids; returns the cleaned answer and ids in order of first use."""
    used: list[str] = []

    def repl(match: re.Match[str]) -> str:
        ids = [i.strip().lower() for i in match.group(1).split(",")]
        valid = [i for i in ids if i in context]
        for i in valid:
            if i not in used:
                used.append(i)
        return "".join(f"[{i}]" for i in valid)

    cleaned = _MARKER.sub(repl, answer)
    cleaned = re.sub(r"[ \t]+([.,;:])", r"\1", cleaned)
    return cleaned.strip(), used


def build_sources(ids: list[str], context: EvidenceContext, snippet_chars: int = 240) -> list[Source]:
    sources: list[Source] = []
    for sid in ids:
        ref = context.get(sid)
        if ref is None:
            continue
        text = " ".join(ref.chunk.text.split())
        snippet = text[:snippet_chars] + ("…" if len(text) > snippet_chars else "")
        sources.append(Source(id=sid, document_id=ref.chunk.document_id, document=ref.chunk.filename,
                              page=ref.chunk.page, snippet=snippet))
    return sources

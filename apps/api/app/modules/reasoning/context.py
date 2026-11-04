"""Numbered excerpt context shared by every LLM step, so citations use one id scheme ([s1], [s2]…)."""

from dataclasses import dataclass

from app.modules.knowledge_base.retrieval.schemas import RetrievedChunk


@dataclass(frozen=True)
class SourceRef:
    sid: str
    chunk: RetrievedChunk


class EvidenceContext:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.refs = [SourceRef(f"s{i}", c) for i, c in enumerate(chunks, start=1)]
        self._by_id = {r.sid: r for r in self.refs}

    def __contains__(self, sid: str) -> bool:
        return sid in self._by_id

    def get(self, sid: str) -> SourceRef | None:
        return self._by_id.get(sid)

    @property
    def ids(self) -> list[str]:
        return [r.sid for r in self.refs]

    def render(self, max_chars_per_chunk: int = 1600) -> str:
        """Excerpts are fenced as quoted data so instructions inside documents aren't followed."""
        blocks = []
        for r in self.refs:
            text = r.chunk.text[:max_chars_per_chunk]
            blocks.append(f'<excerpt id="{r.sid}" document="{r.chunk.filename}" page="{r.chunk.page}">\n'
                          f"{text}\n</excerpt>")
        return "\n\n".join(blocks)

from dataclasses import dataclass

from llama_index.core.node_parser import SentenceSplitter

from app.modules.knowledge_base.ingestion.extractor import PageText


@dataclass(frozen=True)
class ChunkDraft:
    page_number: int
    chunk_index: int
    text: str


class PageAwareChunker:
    """Splits each page independently so every chunk maps to exactly one page for citations."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                          paragraph_separator="\n\n")

    def chunk(self, pages: list[PageText]) -> list[ChunkDraft]:
        drafts: list[ChunkDraft] = []
        for page in pages:
            for piece in self._splitter.split_text(page.text):
                piece = piece.strip()
                if len(piece) >= 20:
                    drafts.append(ChunkDraft(page.page_number, len(drafts), piece))
        return drafts

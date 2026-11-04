from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    id: str
    document_id: str
    filename: str
    page: int
    text: str
    vector_score: float | None = None   # cosine similarity (0..1)
    keyword_rank: float | None = None   # Postgres ts_rank
    fused_score: float = 0.0            # reciprocal-rank fusion

    @property
    def reference(self) -> str:
        return f"{self.filename} — Page {self.page}"


class RetrievalResult(BaseModel):
    chunks: list[RetrievedChunk]
    top_similarity: float
    keyword_hits: int

"""The only read path into the knowledge base. Every query is filtered by org_id."""

import asyncio
import logging
import uuid

from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
)
from llama_index.vector_stores.postgres import PGVectorStore

from app.infra.embeddings.base import EmbeddingProvider
from app.modules.knowledge_base.retrieval.fusion import reciprocal_rank_fusion
from app.modules.knowledge_base.retrieval.schemas import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)


def _org_filter(org_id: uuid.UUID) -> MetadataFilters:
    return MetadataFilters(
        filters=[MetadataFilter(key="org_id", value=str(org_id), operator=FilterOperator.EQ)]
    )


class RetrievalService:
    def __init__(self, store: PGVectorStore, embeddings: EmbeddingProvider, top_k: int) -> None:
        self.store = store
        self.embeddings = embeddings
        self.top_k = top_k

    async def retrieve(self, org_id: uuid.UUID, query: str, top_k: int | None = None) -> RetrievalResult:
        """Hybrid search: dense (pgvector cosine) + sparse (Postgres full-text), fused with RRF."""
        k = top_k or self.top_k
        filters = _org_filter(org_id)
        embedding = await self.embeddings.embed_query(query)

        dense, sparse = await asyncio.gather(
            self.store.aquery(VectorStoreQuery(query_embedding=embedding, similarity_top_k=k * 2,
                                               filters=filters, mode=VectorStoreQueryMode.DEFAULT)),
            self.store.aquery(VectorStoreQuery(query_str=query, similarity_top_k=k * 2, sparse_top_k=k * 2,
                                               filters=filters, mode=VectorStoreQueryMode.TEXT_SEARCH)),
        )

        chunks: dict[str, RetrievedChunk] = {}
        for result, field in ((dense, "vector_score"), (sparse, "keyword_rank")):
            for node, score in zip(result.nodes or [], result.similarities or [], strict=False):
                meta = node.metadata or {}
                # Defence in depth: never trust a row that isn't stamped with this org.
                if meta.get("org_id") != str(org_id):
                    logger.error("Dropped chunk %s with foreign org_id during retrieval", node.node_id)
                    continue
                chunk = chunks.get(node.node_id) or RetrievedChunk(
                    id=node.node_id,
                    document_id=str(node.ref_doc_id or meta.get("doc_id")),
                    filename=str(meta.get("filename", "document.pdf")),
                    page=int(meta.get("page", 0)),
                    text=node.get_content(),
                )
                setattr(chunk, field, float(score))
                chunks[node.node_id] = chunk

        fused = reciprocal_rank_fusion([
            [n.node_id for n in dense.nodes or [] if n.node_id in chunks],
            [n.node_id for n in sparse.nodes or [] if n.node_id in chunks],
        ])
        for chunk_id, score in fused.items():
            chunks[chunk_id].fused_score = score

        ranked = sorted(chunks.values(), key=lambda c: c.fused_score, reverse=True)[:k]
        return RetrievalResult(
            chunks=ranked,
            top_similarity=max((c.vector_score or 0.0 for c in chunks.values()), default=0.0),
            keyword_hits=sum(1 for c in chunks.values() if c.keyword_rank),
        )

    async def retrieve_many(self, org_id: uuid.UUID, queries: list[str], per_query_k: int) -> RetrievalResult:
        """Parallel sub-queries (e.g. each side of a comparison), merged and de-duplicated."""
        results = await asyncio.gather(*(self.retrieve(org_id, q, per_query_k) for q in queries))
        merged: dict[str, RetrievedChunk] = {}
        for result in results:
            for chunk in result.chunks:
                if chunk.id not in merged or chunk.fused_score > merged[chunk.id].fused_score:
                    merged[chunk.id] = chunk
        # Interleave so each sub-query keeps representation in the context window.
        ordered: list[RetrievedChunk] = []
        seen: set[str] = set()
        for i in range(per_query_k):
            for result in results:
                if i < len(result.chunks) and result.chunks[i].id not in seen:
                    seen.add(result.chunks[i].id)
                    ordered.append(merged[result.chunks[i].id])
        return RetrievalResult(
            chunks=ordered,
            top_similarity=min((r.top_similarity for r in results), default=0.0),
            keyword_hits=sum(r.keyword_hits for r in results),
        )

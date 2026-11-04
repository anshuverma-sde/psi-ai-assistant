import asyncio
import logging
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


class FastEmbedProvider:
    """Local, free ONNX embeddings (default: BAAI/bge-small-en-v1.5, 384-d)."""

    def __init__(self, model_name: str, dim: int, cache_dir: Path | None = None) -> None:
        self.model_name = model_name
        self.dim = dim
        logger.info("Loading embedding model %s", model_name)
        self._model = TextEmbedding(model_name=model_name, cache_dir=str(cache_dir) if cache_dir else None)

    @staticmethod
    def _normalize(vectors: list[np.ndarray]) -> list[list[float]]:
        out = []
        for v in vectors:
            norm = float(np.linalg.norm(v)) or 1.0
            out.append((v / norm).astype(float).tolist())
        return out

    def embed_documents_sync(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._normalize(list(self._model.passage_embed(texts, batch_size=32)))

    def embed_query_sync(self, text: str) -> list[float]:
        return self._normalize(list(self._model.query_embed([text])))[0]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query_sync, text)

"""Composition root: builds long-lived services once per process."""

import logging
from dataclasses import dataclass

from llama_index.vector_stores.postgres import PGVectorStore

from app.core.config import Settings
from app.infra.db.session import Database
from app.infra.embeddings.base import EmbeddingProvider
from app.infra.embeddings.fastembed_provider import FastEmbedProvider
from app.infra.llm.base import LLMProvider
from app.infra.llm.factory import create_llm_provider
from app.infra.storage.base import FileStorage
from app.infra.storage.local_disk import LocalDiskStorage
from app.infra.vector_store.pgvector import create_vector_store
from app.modules.reasoning.graph.builder import AskGraph, build_ask_graph
from app.modules.reasoning.understanding.classifier.model import QuestionClassifier

logger = logging.getLogger(__name__)


@dataclass
class Container:
    settings: Settings
    db: Database
    storage: FileStorage
    embeddings: EmbeddingProvider
    vector_store: PGVectorStore
    llm: LLMProvider
    classifier: QuestionClassifier
    ask_graph: AskGraph


def build_container(settings: Settings, *, llm: LLMProvider | None = None) -> Container:
    embeddings = FastEmbedProvider(settings.embedding_model, settings.embedding_dim,
                                   settings.embedding_cache_dir)
    vector_store = create_vector_store(settings.database_url, settings.vector_table,
                                       settings.embedding_dim)
    llm = llm or create_llm_provider(settings)
    classifier = QuestionClassifier.load_or_train(embeddings, settings.embedding_model)
    container = Container(
        settings=settings,
        db=Database(settings.database_url),
        storage=LocalDiskStorage(settings.storage_dir),
        embeddings=embeddings,
        vector_store=vector_store,
        llm=llm,
        classifier=classifier,
        ask_graph=None,  # type: ignore[arg-type]  # set below; graph needs the container's services
    )
    container.ask_graph = build_ask_graph(container)
    logger.info("Container ready (llm=%s, embeddings=%s)", llm.name, settings.embedding_model)
    return container

import uuid

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.vector_stores.postgres import PGVectorStore

from app.infra.embeddings.base import EmbeddingProvider
from app.modules.knowledge_base.ingestion.chunker import ChunkDraft


def embedding_text(filename: str, draft: ChunkDraft) -> str:
    """What we embed: the chunk plus its document title, which helps title-ish questions."""
    title = filename.rsplit(".", 1)[0].replace("_", " ")
    return f"{title}\n{draft.text}"


async def build_nodes(
    drafts: list[ChunkDraft],
    embeddings: EmbeddingProvider,
    *,
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    filename: str,
) -> list[TextNode]:
    vectors = await embeddings.embed_documents([embedding_text(filename, d) for d in drafts])
    nodes: list[TextNode] = []
    for draft, vector in zip(drafts, vectors, strict=True):
        node = TextNode(
            id_=str(uuid.uuid4()),
            text=draft.text,
            embedding=vector,
            metadata={
                # org_id is stamped on every chunk; retrieval always filters on it.
                "org_id": str(org_id),
                "filename": filename,
                "page": draft.page_number,
                "chunk_index": draft.chunk_index,
            },
        )
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=str(document_id))
        nodes.append(node)
    return nodes


async def index_nodes(store: PGVectorStore, nodes: list[TextNode]) -> None:
    if nodes:
        await store.async_add(nodes)


async def delete_document_vectors(store: PGVectorStore, document_id: uuid.UUID) -> None:
    await store.adelete(ref_doc_id=str(document_id))

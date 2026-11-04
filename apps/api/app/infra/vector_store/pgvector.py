from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy.engine import make_url


def create_vector_store(database_url: str, table_name: str, embed_dim: int) -> PGVectorStore:
    """LlamaIndex-managed chunk table (`data_<table_name>`) with vector + full-text columns.

    `org_id` and `doc_id` metadata keys are indexed because every query filters on them.
    """
    url = make_url(database_url)
    sync_url = url.set(drivername="postgresql+psycopg2")
    async_url = url.set(drivername="postgresql+asyncpg")
    return PGVectorStore.from_params(
        connection_string=sync_url.render_as_string(hide_password=False),
        async_connection_string=async_url.render_as_string(hide_password=False),
        table_name=table_name,
        embed_dim=embed_dim,
        hybrid_search=True,
        text_search_config="english",
        use_jsonb=True,
        hnsw_kwargs={"hnsw_m": 16, "hnsw_ef_construction": 64, "hnsw_ef_search": 40,
                     "hnsw_dist_method": "vector_cosine_ops"},
        indexed_metadata_keys={("org_id", "text"), ("doc_id", "text")},
    )

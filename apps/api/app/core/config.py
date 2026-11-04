from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # The API reads only its own env file (apps/api/.env); real environment variables take precedence.
    model_config = SettingsConfigDict(env_file=API_ROOT / ".env", extra="ignore")

    app_name: str = "PSI Knowledge Assistant"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://psi:psi@localhost:5433/psi"

    # Auth
    jwt_secret: str = "dev-only-change-me-please-32-bytes-min"
    jwt_expires_minutes: int = 60 * 12
    session_cookie_name: str = "psi_session"
    cookie_secure: bool = False

    # Public URLs (used to build assistant links and embed code)
    public_app_url: str = "http://localhost:3000"

    # Storage
    storage_dir: Path = API_ROOT / "storage"

    # Knowledge-base limits
    max_documents: int = 10
    max_pages: int = 20
    max_file_mb: int = 10

    # Embeddings / vector store
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    embedding_cache_dir: Path = API_ROOT / ".cache" / "fastembed"
    vector_table: str = "kb_chunks"
    chunk_size: int = 350
    chunk_overlap: int = 60

    # Retrieval + answerability gate (tuned on samples/test_questions.json)
    retrieval_top_k: int = 6
    gate_strong_similarity: float = 0.74
    gate_min_similarity: float = 0.62

    # LLM
    llm_provider: Literal["groq", "ollama"] = "groq"
    groq_api_key: str | None = None
    llm_model: str = "openai/gpt-oss-120b"
    # Comma-separated, tried in order when the primary model is rate-limited (each has its own free quota).
    llm_fallback_models: str = "openai/gpt-oss-20b,qwen/qwen3.8-27b"
    llm_reasoning_effort: Literal["low", "medium", "high"] = "low"
    llm_timeout_s: float = 45.0
    llm_max_retries: int = 2
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Public assistant API
    max_question_chars: int = 1000
    ask_rate_limit: str = "30/minute"

    @property
    def llm_fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.llm_fallback_models.split(",") if m.strip()]

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()

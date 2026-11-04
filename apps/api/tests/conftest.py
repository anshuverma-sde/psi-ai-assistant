"""Test setup: separate `psi_test` database, real embeddings + pgvector, fake (scripted) LLM."""

import os
import tempfile

os.environ.update({
    "APP_ENV": "test",
    "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://psi:psi@localhost:5433/psi_test"),
    "VECTOR_TABLE": "kb_chunks_test",
    "STORAGE_DIR": tempfile.mkdtemp(prefix="psi-test-storage-"),
    "LOG_LEVEL": "WARNING",
    "JWT_SECRET": "test-secret-test-secret-test-secret-1234",
    "PUBLIC_APP_URL": "http://testserver",
})

import uuid  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.container import build_container  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.infra.db.registry import Base  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.fakes import FakeLLM  # noqa: E402
from tests.pdf_factory import make_pdf  # noqa: E402


@pytest.fixture(scope="session")
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture(scope="session")
async def container(fake_llm):
    settings = get_settings()
    c = build_container(settings, llm=fake_llm)
    async with c.db.engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text(f"DROP TABLE IF EXISTS data_{settings.vector_table}"))
        await conn.run_sync(Base.metadata.create_all)
    yield c
    await c.db.dispose()


@pytest.fixture(scope="session")
async def app(container):
    application = create_app(container=container)
    application.state.container = container  # ASGITransport doesn't run lifespan
    return application


@pytest.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver",
                                 timeout=120) as c:
        yield c


async def register_org(app, name: str) -> httpx.AsyncClient:
    """Returns a logged-in client (cookie jar) for a fresh organization."""
    c = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver", timeout=120)
    resp = await c.post("/api/auth/register", json={
        "organization_name": name, "email": f"{uuid.uuid4().hex[:10]}@example.com", "password": "Password123!",
    })
    assert resp.status_code == 201, resp.text
    return c


async def upload(c: httpx.AsyncClient, filename: str, data: bytes) -> httpx.Response:
    return await c.post("/api/admin/documents", files={"file": (filename, data, "application/pdf")})


async def assistant_token(c: httpx.AsyncClient) -> str:
    return (await c.get("/api/admin/assistant")).json()["data"]["token"]


@pytest.fixture
def pdf():
    return make_pdf

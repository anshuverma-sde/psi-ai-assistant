import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.container import Container, build_container
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.rate_limit import limiter
from app.core.responses.handlers import register_exception_handlers
from app.infra.llm.base import LLMProvider
from app.modules.analytics.router import router as analytics_router
from app.modules.assistant.public.router import router as public_assistant_router
from app.modules.assistant.token.router import router as assistant_router
from app.modules.auth.router import router as auth_router
from app.modules.knowledge_base.documents.router import router as documents_router
from app.modules.knowledge_base.ingestion.service import IngestionService
from app.modules.system.router import router as system_router

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, *, llm: LLMProvider | None = None,
               container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = container or await asyncio.to_thread(build_container, settings, llm=llm)
        if not settings.is_test:
            # Resume documents interrupted by a restart, without blocking startup.
            app.state.resume_task = asyncio.create_task(
                IngestionService(app.state.container).resume_pending())
        yield
        if container is None:
            await app.state.container.db.dispose()

    app = FastAPI(
        title="PSI — AI Knowledge & Decision Assistant API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.state.limiter = limiter
    limiter.enabled = not settings.is_test
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    for router in (system_router, auth_router, documents_router, assistant_router,
                   public_assistant_router, analytics_router):
        app.include_router(router)
    return app


app = create_app()

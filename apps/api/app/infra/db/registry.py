"""Imports every ORM model so `Base.metadata` is complete (Alembic, tests)."""

from app.infra.db.base import Base
from app.modules.analytics.models import QueryLog
from app.modules.assistant.models import Assistant
from app.modules.auth.models import User
from app.modules.knowledge_base.documents.models import Document
from app.modules.organization.models import Organization

__all__ = ["Base", "Assistant", "Document", "Organization", "QueryLog", "User"]

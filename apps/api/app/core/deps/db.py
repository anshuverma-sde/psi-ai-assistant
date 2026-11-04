from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.container import Container


def get_container(request: Request) -> "Container":
    return request.app.state.container


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with get_container(request).db.session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]

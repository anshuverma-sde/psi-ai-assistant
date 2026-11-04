from typing import Protocol


class FileStorage(Protocol):
    """Private blob storage for uploaded PDFs. Nothing here is ever served publicly."""

    async def save(self, key: str, data: bytes) -> None: ...

    async def read(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...

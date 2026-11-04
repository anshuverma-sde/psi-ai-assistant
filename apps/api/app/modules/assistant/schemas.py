from datetime import datetime

from pydantic import BaseModel


class EmbedCode(BaseModel):
    iframe: str
    script: str


class AssistantOut(BaseModel):
    token: str
    assistant_url: str
    rotated_at: datetime
    embed: EmbedCode

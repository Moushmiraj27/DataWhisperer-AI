from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage] = Field(default_factory=list)


class ResetConversationResponse(BaseModel):
    session_id: str
    reset: bool

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.conversation import ConversationMode, MessageRole


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=255)
    mode: ConversationMode = ConversationMode.GENERAL


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    mode: ConversationMode
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    provider: str | None
    model: str | None
    routing_reason: str | None
    created_at: datetime


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=16_000)
    mode: ConversationMode = ConversationMode.GENERAL
    force_provider: str | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageRead

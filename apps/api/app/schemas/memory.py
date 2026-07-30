import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.memory import MemoryTier


class MemoryCreate(BaseModel):
    tier: MemoryTier
    summary: str = Field(min_length=1, max_length=4_000)
    project_ref: str | None = Field(default=None, max_length=64)
    source_conversation_id: uuid.UUID | None = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tier: MemoryTier
    project_ref: str | None
    summary: str
    importance: float
    created_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    tiers: list[MemoryTier] | None = None
    project_ref: str | None = None
    limit: int = Field(default=8, ge=1, le=50)


class MemorySearchResult(BaseModel):
    memory: MemoryRead
    score: float

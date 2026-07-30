import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.book import BookLanguage


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    author_name: str = Field(min_length=1, max_length=255)
    language: BookLanguage = BookLanguage.EN


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    subtitle: str | None
    author_name: str
    language: BookLanguage
    created_at: datetime
    updated_at: datetime


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    order_index: int = Field(ge=0)
    content_markdown: str = ""


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    order_index: int | None = Field(default=None, ge=0)
    content_markdown: str | None = None


class ChapterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_index: int
    title: str
    content_markdown: str
    updated_at: datetime


class BookWithChapters(BookRead):
    chapters: list[ChapterRead] = []

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.book import BookLanguage

# Audit finding: `content_markdown` was an unbounded Text column with no
# application-level cap — a single request could store an arbitrarily large
# chapter (megabytes of markdown), and PDF export renders every chapter in
# one process, so unbounded input size is also unbounded rendering cost.
# ~200k characters is generously above any real book chapter (tens of
# thousands of words) while still being a real, enforced ceiling.
MAX_CHAPTER_CONTENT_CHARS = 200_000


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
    content_markdown: str = Field(default="", max_length=MAX_CHAPTER_CONTENT_CHARS)


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    order_index: int | None = Field(default=None, ge=0)
    content_markdown: str | None = Field(default=None, max_length=MAX_CHAPTER_CONTENT_CHARS)


class ChapterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_index: int
    title: str
    content_markdown: str
    updated_at: datetime


class BookWithChapters(BookRead):
    chapters: list[ChapterRead] = []

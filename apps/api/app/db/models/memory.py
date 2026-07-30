import enum
import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_utils import pg_enum
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MemoryTier(str, enum.Enum):
    """The four memory tiers described in the StromeX Editorial Bible, Part VII."""

    CONVERSATION = "conversation"  # ephemeral, scoped to a single conversation
    PROJECT = "project"            # scoped to a book/quran-plan/workspace
    USER = "user"                  # durable facts about the user, across everything
    LONG_TERM = "long_term"        # distilled, high-confidence knowledge retained indefinitely


class MemoryItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Postgres system-of-record for a memory; the embedding vector itself lives in Qdrant,
    keyed by `qdrant_point_id`, so this row can be listed/edited/deleted without touching
    the vector store, and the vector store never holds anything not represented here."""

    __tablename__ = "memory_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[MemoryTier] = mapped_column(pg_enum(MemoryTier, "memory_tier"), nullable=False)
    project_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    qdrant_point_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="memory_items")

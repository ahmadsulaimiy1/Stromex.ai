import enum
import uuid

from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_utils import pg_enum
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ConversationMode(str, enum.Enum):
    GENERAL = "general"
    RESEARCH = "research"
    QURAN = "quran"
    ARABIC_LEARNING = "arabic_learning"
    BOOK_WRITING = "book_writing"


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        # Serves `list_conversations`'s "WHERE user_id = ? ORDER BY updated_at
        # DESC" directly from the index — a lone user_id index would still
        # need a separate sort step once a user has more than a page of rows.
        Index("ix_conversations_user_updated", "user_id", "updated_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="New conversation", nullable=False)
    mode: Mapped[ConversationMode] = mapped_column(
        pg_enum(ConversationMode, "conversation_mode"), default=ConversationMode.GENERAL, nullable=False
    )
    is_archived: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        # Every read of a conversation's messages filters by conversation_id
        # and orders by created_at — this composite index serves both parts
        # of that query without a separate sort.
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MessageRole] = mapped_column(pg_enum(MessageRole, "message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    routing_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

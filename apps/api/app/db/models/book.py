import enum
import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_utils import pg_enum
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class BookLanguage(str, enum.Enum):
    EN = "en"
    AR = "ar"
    BILINGUAL = "bilingual"


class Book(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "books"
    __table_args__ = (Index("ix_books_user_updated", "user_id", "updated_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[BookLanguage] = mapped_column(
        pg_enum(BookLanguage, "book_language"), default=BookLanguage.EN, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="books")
    chapters: Mapped[list["BookChapter"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="BookChapter.order_index"
    )


class BookChapter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "book_chapters"
    __table_args__ = (Index("ix_book_chapters_book_order", "book_id", "order_index"),)

    book_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, default="", nullable=False)

    book: Mapped["Book"] = relationship(back_populates="chapters")

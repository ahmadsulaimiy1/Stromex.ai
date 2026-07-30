import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_utils import pg_enum
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class QuranPlanType(str, enum.Enum):
    MEMORIZATION = "memorization"
    REVISION = "revision"


class QuranPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quran_plans"
    __table_args__ = (Index("ix_quran_plans_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_type: Mapped[QuranPlanType] = mapped_column(
        pg_enum(QuranPlanType, "quran_plan_type"), nullable=False
    )
    surah_start: Mapped[int] = mapped_column(Integer, nullable=False)
    ayah_start: Mapped[int] = mapped_column(Integer, nullable=False)
    surah_end: Mapped[int] = mapped_column(Integer, nullable=False)
    ayah_end: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_target_ayahs: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="quran_plans")
    items: Mapped[list["QuranRevisionItem"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class QuranRevisionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One spaced-repetition unit (an ayah range) scheduled with the SM-2 algorithm.

    See app.services.spaced_repetition for the scheduling logic itself — this row only
    stores the SM-2 state (ease factor, interval, repetitions, due date).
    """

    __tablename__ = "quran_revision_items"
    __table_args__ = (
        # `get_due_items` filters plan_id and orders by due_at; this composite
        # index serves both without a separate sort as a plan's item count grows.
        Index("ix_quran_revision_items_plan_due", "plan_id", "due_at"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("quran_plans.id", ondelete="CASCADE"), nullable=False
    )
    surah: Mapped[int] = mapped_column(Integer, nullable=False)
    ayah_start: Mapped[int] = mapped_column(Integer, nullable=False)
    ayah_end: Mapped[int] = mapped_column(Integer, nullable=False)

    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)

    plan: Mapped["QuranPlan"] = relationship(back_populates="items")
    logs: Mapped[list["QuranReviewLog"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class QuranReviewLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only log of every review event, powering learning analytics."""

    __tablename__ = "quran_review_logs"
    __table_args__ = (
        # `compute_analytics` filters "item_id IN (...) AND created_at >= ?" —
        # this composite index serves that range scan directly.
        Index("ix_quran_review_logs_item_created", "item_id", "created_at"),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quran_revision_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # SM-2 quality, 0-5
    interval_before: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_after: Mapped[int] = mapped_column(Integer, nullable=False)
    ease_factor_after: Mapped[float] = mapped_column(Float, nullable=False)

    item: Mapped["QuranRevisionItem"] = relationship(back_populates="logs")

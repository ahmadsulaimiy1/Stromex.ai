import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
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

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("quran_plans.id", ondelete="CASCADE"), nullable=False, index=True
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

    item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quran_revision_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # SM-2 quality, 0-5
    interval_before: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_after: Mapped[int] = mapped_column(Integer, nullable=False)
    ease_factor_after: Mapped[float] = mapped_column(Float, nullable=False)

    item: Mapped["QuranRevisionItem"] = relationship(back_populates="logs")

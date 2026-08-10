"""What an institution has bought, what it has switched on, and what it has used.

Four tables and four different questions, kept apart because the answers differ
and a system that merges them can only give one:

  `plans` / `plan_features` / `plan_limits` — what a plan *includes*. Platform
  rows, not tenant rows: a plan is EdirasX's product, and a school that could
  edit its own plan would be editing its own bill.

  `subscriptions` — which plan this institution is on, and in what state.

  `subscription_overrides` — what we have granted this institution beyond its
  plan, with a reason and usually an expiry. Every real business does this; a
  system without a place for it grows a fork of the plan table instead.

  `feature_settings` — what the institution has switched **off** for itself.
  Distinct from not having bought it, and the distinction is not cosmetic: "your
  plan does not include this, here is how to upgrade" and "your administrator
  turned this off" are different sentences said to different people, and telling
  a teacher the first when the second is true sends them to the wrong place.

  `usage_records` — what has been consumed this period.

`plans` and its children are the only non-tenant-owned tables here, and they say
so in their docstrings for the same reason `Tenant` and `User` do.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class SubscriptionStatus(str, enum.Enum):
    """The states a subscription can be in, and each one's effect on access.

    `past_due` deliberately still entitles. A school whose card expired must not
    lose the register on Monday morning; the failure is a commercial problem and
    solving it by withholding a child's attendance record would be indefensible.
    Dunning belongs in a workflow, not in an authorization check.
    """

    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    paused = "paused"
    canceled = "canceled"

    @property
    def entitles(self) -> bool:
        return self in {
            SubscriptionStatus.trialing,
            SubscriptionStatus.active,
            SubscriptionStatus.past_due,
        }


class Plan(UUIDPrimaryKey, Timestamped, Base):
    """A product EdirasX sells. **Not tenant-owned.**

    Deliberately outside the tenant boundary: a plan belongs to the platform,
    every school reads the same rows, and a school able to write to its own plan
    would be able to grant itself anything. The features and limits below
    inherit that.
    """

    __tablename__ = "plans"

    key: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Ordering for display and for "is this an upgrade?" — meaningful only
    # within EdirasX's own range, like a qualification's framework level.
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    features: Mapped[list[PlanFeature]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )
    limits: Mapped[list[PlanLimit]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )


class PlanFeature(UUIDPrimaryKey, Timestamped, Base):
    """Whether a plan includes a capability. Not tenant-owned (see `Plan`)."""

    __tablename__ = "plan_features"
    __table_args__ = (
        UniqueConstraint("plan_id", "feature_key", name="uq_plan_features_plan_key"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    plan: Mapped[Plan] = relationship(back_populates="features")


class PlanLimit(UUIDPrimaryKey, Timestamped, Base):
    """A ceiling a plan imposes. `value IS NULL` means unlimited.

    Null rather than a sentinel number, because every sentinel is a number
    somebody eventually reaches. `0` means genuinely none, and the two must not
    be confusable.
    """

    __tablename__ = "plan_limits"
    __table_args__ = (
        UniqueConstraint("plan_id", "limit_key", name="uq_plan_limits_plan_key"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    # A limit key or a meter key: a ceiling on a standing quantity and a ceiling
    # on a period's consumption are both "how much", and the difference is in
    # how they are *measured*, which the service knows and this row need not.
    limit_key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(16, 3))

    plan: Mapped[Plan] = relationship(back_populates="limits")


class Subscription(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """Which plan this institution is on."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_tenant_status", "tenant_id", "status"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.trialing,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    interval: Mapped[str] = mapped_column(String(16), nullable=False, default="month")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubscriptionOverride(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """Something granted to this institution beyond its plan, with a reason.

    Not a loophole — a fact of the business. Pilots, migrations, apologies and
    negotiated contracts all produce "this school has that, and here is why".
    A system with nowhere to record it grows a duplicate plan per school
    instead, and nobody can then answer what any plan actually includes.

    `expires_at` is nullable but usually set: a grant nobody revisits becomes
    permanent by accident.
    """

    __tablename__ = "subscription_overrides"
    __table_args__ = (
        Index("ix_subscription_overrides_tenant_key", "tenant_id", "key"),
    )

    # A feature key, a limit key, or a meter key.
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    # For a feature: true/false. For a limit or meter: the replacement ceiling,
    # or null meaning unlimited.
    enabled: Mapped[bool | None] = mapped_column(Boolean)
    value: Mapped[float | None] = mapped_column(Numeric(16, 3))
    # Distinguishes "unlimited" from "no value given", which `value IS NULL`
    # alone cannot.
    is_unlimited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def is_live(self, now: datetime) -> bool:
        return self.expires_at is None or self.expires_at > now


class FeatureSetting(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """What the institution has switched off for itself.

    The fourth question, and the one most systems never ask. A school on a plan
    that includes the AI assistants may have decided not to use them; that is
    the school's decision and it is not a billing state. Keeping it separate is
    what lets the product say "your administrator turned this off" rather than
    "upgrade your plan" — a sentence that would send a teacher to the wrong
    person and imply a cost that does not exist.

    A row here can only *disable*. Enabling something the plan does not include
    is not an institution's decision to make, and allowing it would put the
    entitlement boundary inside the tenant.
    """

    __tablename__ = "feature_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "feature_key", name="uq_feature_settings_key"),
    )

    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    changed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    note: Mapped[str | None] = mapped_column(Text)


class UsageRecord(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One consumption event, in one period.

    Append-only in practice and aggregated on read rather than kept as a
    running total, because a counter is a number nobody can audit: when a school
    disputes its AI bill, the answer has to be a list of what was spent, by
    whom, on what, and when.
    """

    __tablename__ = "usage_records"
    __table_args__ = (
        Index("ix_usage_records_tenant_meter_period", "tenant_id", "meter_key",
              "period_start"),
    )

    meter_key: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(16, 3), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    feature_key: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


__all__ = [
    "FeatureSetting",
    "Plan",
    "PlanFeature",
    "PlanLimit",
    "Subscription",
    "SubscriptionOverride",
    "SubscriptionStatus",
    "UsageRecord",
]

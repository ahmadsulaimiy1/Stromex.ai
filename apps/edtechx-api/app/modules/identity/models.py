"""Identity: people, their credentials, their membership of a school.

A `User` is global — one human, one credential, even when they teach at two
schools. A `Membership` is the tenant-scoped join, and *everything* about
authorization hangs off the membership rather than the user. That separation is
what makes "a teacher at two schools" work without ever giving one school a
window into the other: switching schools re-mints the token against a different
membership, and the session itself is tenant-bound.
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
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class UserStatus(str, enum.Enum):
    invited = "invited"
    active = "active"
    suspended = "suspended"
    deactivated = "deactivated"


class MembershipStatus(str, enum.Enum):
    invited = "invited"
    active = "active"
    suspended = "suspended"
    ended = "ended"


class User(UUIDPrimaryKey, Timestamped, Base):
    """A human. Not tenant-owned: one person, one credential, many schools."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True, index=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_hash: Mapped[str | None] = mapped_column(Text)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"), nullable=False, default=UserStatus.invited
    )
    locale: Mapped[str | None] = mapped_column(String(16))

    # MFA — the secret is application-encrypted before it reaches this column
    # (EDTECHX_SECURITY.md §4). The column name says so to keep it obvious at
    # every call site.
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(Text)
    mfa_enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Brute-force protection. Kept on the user, not only in Redis, so that a
    # cache flush cannot reset an attacker's budget.
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Platform staff. Never grants access to tenant content — that requires a
    # break-glass grant (EDTECHX_ARCHITECTURE.md §9).
    is_platform_operator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")

    @property
    def has_mfa(self) -> bool:
        return self.mfa_enabled_at is not None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.email}>"


class Membership(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A person's place in one school. The unit authorization is built on."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_id_user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, name="membership_status"),
        nullable=False,
        default=MembershipStatus.invited,
    )
    display_name: Mapped[str | None] = mapped_column(String(200))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="memberships")
    # Deliberately no `role_grants` back-reference. Role grants belong to the
    # authz module; identity does not import it, and a membership's authority
    # is read through authz's service layer (EDTECHX_ARCHITECTURE.md §3).

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.active


class UserSession(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A refresh-token family.

    Only the hash is stored. Rotation on every use with reuse detection means a
    stolen refresh token is usable at most once, and its use burns the whole
    family — see EDTECHX_SECURITY.md §2.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(64))
    rotated_from_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(512))

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

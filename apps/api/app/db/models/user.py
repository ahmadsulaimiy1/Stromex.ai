import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_utils import pg_enum
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    # Nullable: guest accounts (created via POST /auth/guest) and
    # Google-only accounts (created via the OAuth callback) have no password
    # of their own until/unless the user sets one.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"), default=UserRole.USER, nullable=False
    )
    preferred_language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Guest accounts get a generated `guest-<uuid>@guest.stromex.ai`
    # sentinel address (never emailed) so `email` can stay NOT NULL/unique
    # for every row rather than special-casing the schema for one auth mode.
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # True for guest/Google accounts (nothing to verify) and for email
    # accounts once they've clicked their verification link.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Google's stable per-account subject id ("sub" claim) — set once a user
    # signs in with Google, whether that's a brand-new account or linking an
    # existing email/password account with a matching email.
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    # Incremented by POST /auth/logout-all. Every access/refresh token embeds
    # the version it was issued under; get_current_user and /auth/refresh
    # both reject a token whose version doesn't match the user's current
    # value — the standard "sign out everywhere" mechanism for stateless
    # JWTs, without needing to enumerate and revoke every outstanding token.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memory_items: Mapped[list["MemoryItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    quran_plans: Mapped[list["QuranPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    books: Mapped[list["Book"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AuthTokenPurpose(str, enum.Enum):
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFY = "email_verify"


class AuthToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single-use, expiring token for a password-reset or email-verify
    link. Only a SHA-256 hash of the raw token is ever stored — the same
    "store the hash, not the secret" pattern already used for refresh-token
    revocation (see `app/core/token_denylist.py`) — so a database read alone
    can never mint a usable reset/verify link."""

    __tablename__ = "auth_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose: Mapped[AuthTokenPurpose] = mapped_column(
        pg_enum(AuthTokenPurpose, "auth_token_purpose"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="auth_tokens")

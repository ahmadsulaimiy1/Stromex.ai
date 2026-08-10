"""Password hashing and token issuance.

Argon2id for new hashes; bcrypt accepted on import from a legacy system and
transparently upgraded on the owner's next successful login, so a migrated
school is not stuck on weaker hashing forever.

No composition rules and no forced rotation — both measurably reduce real-world
password strength by pushing people toward predictable patterns. Length plus a
breached-corpus check is what actually works (ADR-012).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from argon2.low_level import Type

from app.core.config import get_settings

TokenType = Literal["access", "refresh"]


# --- passwords ------------------------------------------------------------

_settings = get_settings()
_hasher = PasswordHasher(
    time_cost=_settings.argon2_time_cost,
    memory_cost=_settings.argon2_memory_cost,
    parallelism=_settings.argon2_parallelism,
    type=Type.ID,
)


class WeakPassword(ValueError):
    pass


def validate_password(password: str) -> str:
    settings = get_settings()
    if len(password) < settings.password_min_length:
        raise WeakPassword(
            f"Password must be at least {settings.password_min_length} characters."
        )
    if len(password) > 1024:
        # Long inputs are a hashing DoS vector, not a strength benefit.
        raise WeakPassword("Password must be at most 1024 characters.")
    return password


def hash_password(password: str) -> str:
    validate_password(password)
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Verify a password, in constant-ish time whether or not a hash exists.

    When the user does not exist (or has no password), we still perform a hash
    verification against a dummy value so that response timing does not reveal
    account existence — EDTECHX_SECURITY.md §2.
    """
    if not stored_hash:
        try:
            _hasher.verify(_DUMMY_HASH, password)
        except (VerifyMismatchError, InvalidHashError):
            pass
        return False
    try:
        return _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except InvalidHashError:
        # A bcrypt hash from an import: not an argon2 hash at all, so yes.
        return True


_DUMMY_HASH = _hasher.hash("edtechx-timing-equalizer")


# --- tokens ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    membership_id: uuid.UUID
    tenant_id: uuid.UUID
    session_id: uuid.UUID
    jti: uuid.UUID
    issued_at: datetime
    expires_at: datetime
    authenticated_at: datetime

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= datetime.now(UTC)


class InvalidToken(ValueError):
    pass


def issue_access_token(
    *,
    user_id: uuid.UUID,
    membership_id: uuid.UUID,
    tenant_id: uuid.UUID,
    session_id: uuid.UUID,
    authenticated_at: datetime | None = None,
) -> tuple[str, AccessTokenClaims]:
    settings = get_settings()
    now = datetime.now(UTC)
    auth_at = authenticated_at or now
    expires = now + timedelta(minutes=settings.access_token_ttl_minutes)
    jti = uuid.uuid4()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "mid": str(membership_id),
        # The tenant claim is checked against the host on every request. A
        # token minted for one school is unusable on another's hostname.
        "tid": str(tenant_id),
        "sid": str(session_id),
        "jti": str(jti),
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "auth_at": int(auth_at.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    claims = AccessTokenClaims(
        user_id=user_id,
        membership_id=membership_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=jti,
        issued_at=now,
        expires_at=expires,
        authenticated_at=auth_at,
    )
    return token, claims


def decode_access_token(token: str) -> AccessTokenClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidToken("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidToken("Token is invalid.") from exc

    if payload.get("typ") != "access":
        raise InvalidToken("Token is not an access token.")

    try:
        return AccessTokenClaims(
            user_id=uuid.UUID(payload["sub"]),
            membership_id=uuid.UUID(payload["mid"]),
            tenant_id=uuid.UUID(payload["tid"]),
            session_id=uuid.UUID(payload["sid"]),
            jti=uuid.UUID(payload["jti"]),
            issued_at=datetime.fromtimestamp(payload["iat"], UTC),
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
            authenticated_at=datetime.fromtimestamp(
                payload.get("auth_at", payload["iat"]), UTC
            ),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise InvalidToken("Token claims are malformed.") from exc


# --- refresh tokens -------------------------------------------------------


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Keyed hash, so a database leak alone does not yield usable tokens."""
    settings = get_settings()
    return hmac.new(
        settings.secret_key.encode(), token.encode(), hashlib.sha256
    ).hexdigest()


def refresh_token_matches(token: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(token), stored_hash)


def is_elevated(authenticated_at: datetime) -> bool:
    """Whether a principal re-authenticated recently enough for a risky action."""
    settings = get_settings()
    age = datetime.now(UTC) - authenticated_at
    return age <= timedelta(minutes=settings.elevation_ttl_minutes)

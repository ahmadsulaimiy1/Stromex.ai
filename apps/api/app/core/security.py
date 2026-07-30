"""Password hashing and JWT issuance/verification.

Hashing calls the `bcrypt` library directly rather than going through passlib's
CryptContext: passlib's one-time backend self-test (`detect_wrap_bug`) trips an
incompatibility with bcrypt>=4.1's stricter 72-byte input enforcement, turning
the first hash call into a hard crash. Calling bcrypt directly avoids that
self-test entirely and removes a layer for no loss of functionality.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.token_denylist import is_revoked

_MAX_PASSWORD_BYTES = 72  # bcrypt's hard input limit


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


def _create_token(
    subject: UUID, token_type: TokenType, expires_delta: timedelta, token_version: int
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "jti": str(uuid4()),
        "ver": token_version,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, token_version: int = 0) -> str:
    settings = get_settings()
    return _create_token(
        user_id, TokenType.ACCESS, timedelta(minutes=settings.access_token_expire_minutes), token_version
    )


def create_refresh_token(user_id: UUID, token_version: int = 0) -> str:
    settings = get_settings()
    return _create_token(
        user_id, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days), token_version
    )


class TokenError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class DecodedToken:
    user_id: UUID
    jti: str
    expires_at: datetime
    token_version: int


def _decode(token: str, expected_type: TokenType) -> DecodedToken:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Token is invalid") from exc

    if payload.get("type") != expected_type.value:
        raise TokenError(f"Expected a {expected_type.value} token")

    try:
        user_id = UUID(payload["sub"])
        jti = payload["jti"]
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    except (KeyError, ValueError) as exc:
        raise TokenError("Token payload is malformed") from exc
    # Tokens issued before "ver" existed have no claim at all; treat that as
    # version 0, same as every user row's own default.
    token_version = payload.get("ver", 0)

    if expected_type is TokenType.REFRESH and is_revoked(jti):
        raise TokenError("Token has been revoked")

    return DecodedToken(user_id=user_id, jti=jti, expires_at=expires_at, token_version=token_version)


def decode_token(token: str, expected_type: TokenType) -> UUID:
    """Back-compat convenience wrapper — most callers only need the subject."""
    return _decode(token, expected_type).user_id


def decode_token_full(token: str, expected_type: TokenType) -> DecodedToken:
    """Used where the caller needs `jti`/expiry too — currently just logout,
    to compute the denylist entry's TTL from the token's own remaining life."""
    return _decode(token, expected_type)

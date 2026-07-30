"""Refresh-token revocation.

Audit finding: refresh tokens were pure stateless JWTs with no way to
invalidate one before its 30-day expiry — a leaked refresh token, or a user
who wants to sign out a device, had no mechanism to actually revoke access.
Access tokens stay stateless (short-lived, 30 minutes, and checking a
denylist on every request would add a Redis round-trip to the hot path for
minimal benefit); only refresh tokens are checked against this denylist,
which is the standard tradeoff for JWT-based auth. The denylist entry's TTL
is set to the token's own remaining lifetime, so it never needs manual
cleanup and never grows unbounded.
"""

from app.core.redis import get_redis

_PREFIX = "revoked-refresh-jti"


def revoke(jti: str, ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    get_redis().set(f"{_PREFIX}:{jti}", "1", ex=ttl_seconds)


def is_revoked(jti: str) -> bool:
    return get_redis().exists(f"{_PREFIX}:{jti}") == 1

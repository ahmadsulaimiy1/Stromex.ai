"""Rate limiting.

A token bucket, because the alternative most people reach for — a fixed window
counter — allows twice the intended burst across a window boundary, which is
exactly the moment a credential-stuffing run would exploit.

Two properties matter more than the algorithm:

**Atomicity.** Read-modify-write across a network round trip is a race, and
under concurrency a racy limiter admits far more than its limit. The Redis
adapter therefore does the whole decision inside one Lua script.

**Tenant scoping.** Every key is prefixed with the tenant. Without that, one
school's traffic consumes another school's allowance, which is a denial of
service across a tenant boundary — the same class of failure as a data leak,
and just as unacceptable.
"""

from __future__ import annotations

import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Policy:
    """A token bucket: `capacity` requests, refilling to full over `per_seconds`."""

    name: str
    capacity: int
    per_seconds: float

    @property
    def refill_per_second(self) -> float:
        return self.capacity / self.per_seconds

    @property
    def ttl_seconds(self) -> int:
        # Long enough that a bucket cannot be reset by letting it expire early,
        # short enough that idle keys do not accumulate.
        return int(self.per_seconds * 2) + 60


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    remaining: int
    retry_after: int
    policy: str

    def __bool__(self) -> bool:
        return self.allowed


# --- policies -------------------------------------------------------------
#
# Sign-in is limited three ways at once — by source, by the address being
# tried, and for the school as a whole — so that neither a single fast attacker
# nor a distributed slow one gets a useful number of attempts.
#
# The per-IP figures are deliberately generous, and the reason is a real
# school rather than a threat model: an entire school sits behind one public
# address, and several hundred people sign in during the ten minutes before
# first lesson. A limiter tuned as though one address meant one person would
# lock out a school every morning at 08:30, be switched off within a week, and
# protect nothing. The tight control is the per-account one, which NAT does not
# affect; account lockout (10 failures) binds before it for a targeted account,
# and this backstops the distributed case.

SIGN_IN_PER_IP = Policy("sign_in.ip", capacity=30, per_seconds=300)
SIGN_IN_PER_ACCOUNT = Policy("sign_in.account", capacity=12, per_seconds=900)
SIGN_IN_PER_TENANT = Policy("sign_in.tenant", capacity=1200, per_seconds=300)
REFRESH_PER_IP = Policy("refresh.ip", capacity=120, per_seconds=300)
UNAUTHENTICATED_PER_IP = Policy("anon.ip", capacity=60, per_seconds=60)
AUTHENTICATED_PER_PRINCIPAL = Policy("auth.principal", capacity=600, per_seconds=60)
WRITE_PER_PRINCIPAL = Policy("write.principal", capacity=120, per_seconds=60)


class RateLimiterUnavailable(RuntimeError):
    """The limiter cannot make a decision.

    Never swallowed. A limiter that fails open is not a limiter, and the
    routes it guards are the most exposed in the product.
    """


class Backend(ABC):
    """A rate-limiting backend."""

    @abstractmethod
    def consume(self, key: str, policy: Policy, cost: int = 1) -> Decision: ...

    @abstractmethod
    def reset(self, key: str) -> None: ...

    @property
    @abstractmethod
    def is_shared(self) -> bool:
        """Whether state is shared across processes.

        A per-process limiter multiplies every limit by the worker count, so
        this is what `require_production_ready` checks.
        """


# --- Redis ----------------------------------------------------------------

# The clock comes from Redis (`TIME`), not from the caller. Application servers
# disagree about the time by seconds; a bucket refilled against a fast server's
# clock hands out tokens that a slow one has not earned.
_LUA = """
local key       = KEYS[1]
local capacity  = tonumber(ARGV[1])
local refill    = tonumber(ARGV[2])
local cost      = tonumber(ARGV[3])
local ttl       = tonumber(ARGV[4])

local clock = redis.call('TIME')
local now = tonumber(clock[1]) + (tonumber(clock[2]) / 1000000)

local bucket = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(bucket[1])
local ts     = tonumber(bucket[2])

if tokens == nil or ts == nil then
  tokens = capacity
  ts = now
end

local elapsed = now - ts
if elapsed < 0 then elapsed = 0 end
tokens = math.min(capacity, tokens + (elapsed * refill))

local allowed = 0
local retry = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
else
  retry = math.ceil((cost - tokens) / refill)
end

redis.call('HSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, ttl)

return {allowed, retry, math.floor(tokens)}
"""


class RedisBackend(Backend):
    def __init__(self, client) -> None:  # type: ignore[no-untyped-def]
        self._client = client
        self._script = client.register_script(_LUA)

    @property
    def is_shared(self) -> bool:
        return True

    def consume(self, key: str, policy: Policy, cost: int = 1) -> Decision:
        try:
            allowed, retry, remaining = self._script(
                keys=[key],
                args=[
                    policy.capacity,
                    policy.refill_per_second,
                    cost,
                    policy.ttl_seconds,
                ],
            )
        except Exception as exc:  # pragma: no cover - exercised by the fail-closed test
            raise RateLimiterUnavailable(str(exc)) from exc
        return Decision(
            allowed=bool(allowed),
            remaining=int(remaining),
            retry_after=max(int(retry), 1) if not allowed else 0,
            policy=policy.name,
        )

    def reset(self, key: str) -> None:
        self._client.delete(key)


# --- in-process -----------------------------------------------------------


class InMemoryBackend(Backend):
    """Single-process backend for development and tests.

    Correct within one process and useless across several, which is why
    `require_production_ready` refuses it outside development. It is not a
    fake: it runs the same token-bucket arithmetic under a lock, so behaviour
    tested against it holds against Redis.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    @property
    def is_shared(self) -> bool:
        return False

    def consume(self, key: str, policy: Policy, cost: int = 1) -> Decision:
        now = time.monotonic()
        with self._lock:
            tokens, ts = self._buckets.get(key, (float(policy.capacity), now))
            tokens = min(
                float(policy.capacity),
                tokens + max(0.0, now - ts) * policy.refill_per_second,
            )
            if tokens >= cost:
                tokens -= cost
                allowed, retry = True, 0
            else:
                allowed = False
                retry = max(1, math.ceil((cost - tokens) / policy.refill_per_second))
            self._buckets[key] = (tokens, now)
            return Decision(allowed, int(tokens), retry, policy.name)

    def reset(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()


# --- keys -----------------------------------------------------------------


def key_for(policy: Policy, identity: str, tenant_id: UUID | None) -> str:
    """Build a tenant-scoped key.

    The tenant segment is not optional and is not the caller's choice. Without
    it, exhausting one school's sign-in budget would exhaust every school's —
    a denial of service that crosses a tenant boundary.
    """
    scope = str(tenant_id) if tenant_id else "platform"
    return f"t:{scope}:rl:{policy.name}:{identity}"


# --- resolution -----------------------------------------------------------

_backend: Backend | None = None


def get_backend() -> Backend:
    global _backend
    if _backend is not None:
        return _backend

    settings = get_settings()
    if settings.redis_url:
        try:
            import redis

            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            _backend = RedisBackend(client)
            logger.info("rate_limiter_backend", backend="redis")
            return _backend
        except Exception as exc:
            if settings.is_production:
                raise RateLimiterUnavailable(
                    "Redis is required in production for rate limiting: "
                    "a per-process limiter multiplies every limit by the worker count."
                ) from exc
            logger.warning("rate_limiter_redis_unavailable", error=str(exc))

    require_production_ready(shared=False)
    _backend = InMemoryBackend()
    logger.warning("rate_limiter_backend", backend="in-memory", shared=False)
    return _backend


def set_backend(backend: Backend | None) -> None:
    """Override the backend. Used by tests to exercise both implementations."""
    global _backend
    _backend = backend


def clear_all() -> None:
    """Drop every bucket. Tests only — never called from application code."""
    backend = get_backend()
    if isinstance(backend, InMemoryBackend):
        backend.clear()
    elif isinstance(backend, RedisBackend):
        for key in backend._client.scan_iter(match="t:*:rl:*", count=500):
            backend._client.delete(key)


def require_production_ready(shared: bool) -> None:
    if not shared and get_settings().is_production:
        raise RateLimiterUnavailable(
            "Refusing to run in production with a per-process rate limiter. "
            "Set EDTECHX_REDIS_URL."
        )


def consume(
    policy: Policy, identity: str, tenant_id: UUID | None, cost: int = 1
) -> Decision:
    return get_backend().consume(key_for(policy, identity, tenant_id), policy, cost)


class SupportsConsume(Protocol):  # pragma: no cover - typing aid
    def consume(self, key: str, policy: Policy, cost: int = 1) -> Decision: ...

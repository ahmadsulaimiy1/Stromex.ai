"""Rate limiting, attacked deliberately.

Three properties are worth more than the happy path, and each is tested against
*both* backends so that behaviour proven in development holds in production:

  * it is atomic under concurrency — a racy limiter admits far more than its
    limit, and reads as working right up until it is needed;
  * it is tenant-scoped — one school must not be able to exhaust another's
    allowance, which would be a denial of service across a tenant boundary;
  * it does not become an existence oracle — a 429 must not distinguish a real
    account from an invented one.
"""

from __future__ import annotations

import concurrent.futures
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.rate_limit import (
    Decision,
    InMemoryBackend,
    Policy,
    RateLimiterUnavailable,
    RedisBackend,
    key_for,
)
from app.main import app
from app.tests.conftest import OWNER_PASSWORD, TenantFixture, requires_db

TIGHT = Policy("test.tight", capacity=10, per_seconds=600)
GENEROUS = Policy("test.generous", capacity=1000, per_seconds=60)


def _redis_backend() -> RedisBackend | None:
    try:
        import redis

        client = redis.Redis.from_url("redis://localhost:6379/15", decode_responses=True)
        client.ping()
        client.flushdb()
        return RedisBackend(client)
    except Exception:
        return None


REDIS = _redis_backend()
BACKENDS = [pytest.param(InMemoryBackend(), id="in-memory")]
if REDIS is not None:
    BACKENDS.append(pytest.param(REDIS, id="redis"))


@pytest.fixture(params=BACKENDS)
def backend(request: pytest.FixtureRequest):
    instance = request.param
    if isinstance(instance, RedisBackend):
        instance._client.flushdb()
    else:
        instance.clear()
    return instance


# --- the algorithm --------------------------------------------------------


def test_a_bucket_allows_exactly_its_capacity(backend) -> None:
    key = key_for(TIGHT, "someone", None)
    allowed = sum(1 for _ in range(TIGHT.capacity + 5) if backend.consume(key, TIGHT))
    assert allowed == TIGHT.capacity


def test_refusal_carries_a_usable_retry_after(backend) -> None:
    key = key_for(TIGHT, "someone", None)
    for _ in range(TIGHT.capacity):
        backend.consume(key, TIGHT)
    decision = backend.consume(key, TIGHT)
    assert not decision.allowed
    assert decision.retry_after >= 1


def test_separate_identities_have_separate_buckets(backend) -> None:
    first = key_for(TIGHT, "first", None)
    second = key_for(TIGHT, "second", None)
    for _ in range(TIGHT.capacity):
        backend.consume(first, TIGHT)
    assert not backend.consume(first, TIGHT)
    assert backend.consume(second, TIGHT), "one identity exhausted another's bucket"


def test_the_limiter_is_atomic_under_concurrency(backend) -> None:
    """The property a naive read-modify-write limiter silently lacks.

    Sixty threads race for ten tokens. A racy implementation hands out more
    than ten and looks entirely fine in a sequential test.
    """
    key = key_for(TIGHT, "stampede", None)
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        results = list(pool.map(lambda _: bool(backend.consume(key, TIGHT)), range(60)))
    assert sum(results) == TIGHT.capacity, (
        f"{sum(results)} requests admitted against a capacity of {TIGHT.capacity} — "
        "the limiter is not atomic under concurrency"
    )


def test_concurrency_across_many_buckets_stays_exact(backend) -> None:
    """Interleaved keys must not bleed into one another under load."""
    identities = [f"user-{i}" for i in range(8)]

    def hit(identity: str) -> bool:
        return bool(backend.consume(key_for(TIGHT, identity, None), TIGHT))

    work = [identity for identity in identities for _ in range(TIGHT.capacity + 4)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        list(pool.map(hit, work))

    for identity in identities:
        assert not backend.consume(key_for(TIGHT, identity, None), TIGHT)


# --- tenant scoping -------------------------------------------------------


def test_keys_are_tenant_scoped() -> None:
    tenant = uuid.uuid4()
    key = key_for(TIGHT, "someone", tenant)
    assert key.startswith(f"t:{tenant}:"), "rate-limit key is not tenant-scoped"
    assert key != key_for(TIGHT, "someone", uuid.uuid4())


def test_one_tenant_cannot_exhaust_another_tenants_allowance(backend) -> None:
    """A denial of service that crosses a tenant boundary is still a breach."""
    a, b = uuid.uuid4(), uuid.uuid4()
    for _ in range(TIGHT.capacity):
        backend.consume(key_for(TIGHT, "same-identity", a), TIGHT)

    assert not backend.consume(key_for(TIGHT, "same-identity", a), TIGHT)
    assert backend.consume(key_for(TIGHT, "same-identity", b), TIGHT), (
        "tenant A exhausted tenant B's allowance — the limiter leaks across tenants"
    )


def test_platform_scope_is_distinct_from_any_tenant() -> None:
    assert key_for(TIGHT, "x", None) != key_for(TIGHT, "x", uuid.uuid4())


# --- failure posture ------------------------------------------------------


class BrokenBackend(InMemoryBackend):
    def consume(self, key: str, policy: Policy, cost: int = 1) -> Decision:
        raise RateLimiterUnavailable("backend is down")


def test_production_refuses_a_per_process_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    """A per-worker limiter multiplies every limit by the worker count."""
    from app.core.config import Settings, get_settings

    production = Settings(
        environment="production",
        secret_key="a" * 48,
        database_url="postgresql+psycopg://app:pw@db.internal:5432/edtechx",
        migration_database_url="postgresql+psycopg://mig:pw@db.internal:5432/edtechx",
        cors_origins=["https://portal.example.edu"],
    )
    monkeypatch.setattr("app.core.rate_limit.get_settings", lambda: production)
    with pytest.raises(RateLimiterUnavailable, match="per-process"):
        rate_limit.require_production_ready(shared=False)
    assert get_settings() is not production  # cache untouched


def test_backends_declare_whether_they_are_shared() -> None:
    assert InMemoryBackend().is_shared is False
    if REDIS is not None:
        assert REDIS.is_shared is True


# --- through the HTTP surface --------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@requires_db
def test_sign_in_is_rate_limited_and_returns_retry_after(
    client: TestClient, school_a: TenantFixture
) -> None:
    limit = rate_limit.SIGN_IN_PER_ACCOUNT.capacity
    statuses = [
        client.post(
            "/api/v1/auth/sign-in",
            headers={"Host": school_a.hostname},
            json={"email": school_a.user.email, "password": "wrong-passphrase-here"},
        ).status_code
        for _ in range(limit + 3)
    ]
    assert 429 in statuses, "sign-in was never rate limited"

    final = client.post(
        "/api/v1/auth/sign-in",
        headers={"Host": school_a.hostname},
        json={"email": school_a.user.email, "password": "wrong-passphrase-here"},
    )
    assert final.status_code == 429
    assert final.json()["error"]["code"] == "rate_limited"
    assert int(final.headers["retry-after"]) >= 1


@requires_db
def test_rate_limiting_does_not_become_an_existence_oracle(
    client: TestClient, school_a: TenantFixture
) -> None:
    """A 429 must not distinguish a real account from an invented one.

    Keying the per-account limit on the *submitted* address rather than on a
    matched account is what makes this hold.
    """

    def exhaust(email: str) -> tuple[int, dict]:
        response = None
        for _ in range(rate_limit.SIGN_IN_PER_ACCOUNT.capacity + 2):
            response = client.post(
                "/api/v1/auth/sign-in",
                headers={"Host": school_a.hostname},
                json={"email": email, "password": "wrong-passphrase-here"},
            )
        assert response is not None
        return response.status_code, response.json()

    real_status, real_body = exhaust(school_a.user.email)
    rate_limit.clear_all()
    fake_status, fake_body = exhaust(f"nobody-{uuid.uuid4().hex}@nowhere.test")

    assert real_status == fake_status == 429
    assert real_body == fake_body


@requires_db
def test_one_school_being_limited_does_not_limit_another(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """The isolation regression this feature could most easily introduce."""
    for _ in range(rate_limit.SIGN_IN_PER_ACCOUNT.capacity + 2):
        client.post(
            "/api/v1/auth/sign-in",
            headers={"Host": school_a.hostname},
            json={"email": school_a.user.email, "password": "wrong-passphrase-here"},
        )

    response = client.post(
        "/api/v1/auth/sign-in",
        headers={"Host": school_b.hostname},
        json={"email": school_b.user.email, "password": OWNER_PASSWORD},
    )
    assert response.status_code == 200, (
        "exhausting school A's sign-in allowance blocked school B — "
        "the limiter is not tenant-scoped end to end"
    )


@requires_db
def test_rate_limiting_runs_after_tenant_resolution(client: TestClient) -> None:
    """An unknown host is still unknown, however many times it is tried.

    Ordering matters: if the limiter ran first it would need a tenant it does
    not have, and its keys could not be tenant-scoped.
    """
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/sign-in",
            headers={"Host": "nobody.edtechx.localhost"},
            json={"email": "a@b.test", "password": "whatever-passphrase"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "unknown_school"


@requires_db
def test_a_limited_route_still_enforces_authentication(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Rate limiting must not have become a substitute for an auth check."""
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": "x" * 40},
    )
    assert response.status_code == 401


@requires_db
def test_rate_limiting_does_not_weaken_tenant_isolation(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """The whole Phase 1 guarantee, re-checked after adding the limiter."""
    signed_in = client.post(
        "/api/v1/auth/sign-in",
        headers={"Host": school_a.hostname},
        json={"email": school_a.user.email, "password": OWNER_PASSWORD},
    )
    assert signed_in.status_code == 200
    token = signed_in.json()["access_token"]

    response = client.get(
        "/api/v1/me",
        headers={"Host": school_b.hostname, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "tenant_mismatch"

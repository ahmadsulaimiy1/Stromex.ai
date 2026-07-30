"""Fixed-window rate limiting backed by Redis.

Audit finding (fixed here): the original implementation read
`request.state.user_id`, which nothing in the codebase ever set — every
"per-user" limit was silently falling back to per-IP, and per-IP alone means
every user behind one NAT/corporate proxy shares a single bucket. User-scoped
limiting now depends directly on `get_current_user`, so FastAPI's own
dependency graph — not a hopeful attribute lookup — guarantees the user is
resolved before the limit is checked.
"""

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request, status

from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.db.models.user import User


def _check_and_increment(key: str, times: int, seconds: int) -> None:
    r = get_redis()
    current = r.incr(key)
    if current == 1:
        r.expire(key, seconds)
    if current > times:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests — please slow down and try again shortly.",
        )


def rate_limit_by_ip(times: int, seconds: int, bucket: str) -> Callable[[Request], None]:
    """For endpoints with no authenticated identity yet (register, login) —
    the only identity available pre-auth is the caller's address."""

    def dependency(request: Request) -> None:
        client_id = request.client.host if request.client else "unknown"
        _check_and_increment(f"ratelimit:{bucket}:ip:{client_id}", times, seconds)

    return dependency


def rate_limit_by_field(
    times: int, seconds: int, bucket: str, field: str
) -> Callable[[Request], Awaitable[None]]:
    """Rate-limits by a field in the JSON body (e.g. `email`) rather than IP —
    stops credential stuffing against one account from many IPs, which a
    pure per-IP limit cannot. Reading the body here is safe: Starlette caches
    the raw body after the first read, so the endpoint's own Pydantic
    parsing downstream sees the same bytes, not a second network read."""

    async def dependency(request: Request) -> None:
        try:
            body = await request.json()
        except ValueError:
            return  # malformed JSON — let the endpoint's own validation reject it
        value = body.get(field)
        if not value:
            return
        _check_and_increment(f"ratelimit:{bucket}:{field}:{value}", times, seconds)

    return dependency


def rate_limit_by_user(times: int, seconds: int, bucket: str) -> Callable[..., None]:
    """For authenticated endpoints — keyed by the real user id, resolved
    through `get_current_user` so ordering is guaranteed rather than assumed."""

    def dependency(user: User = Depends(get_current_user)) -> None:
        _check_and_increment(f"ratelimit:{bucket}:user:{user.id}", times, seconds)

    return dependency

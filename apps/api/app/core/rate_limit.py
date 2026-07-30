"""Fixed-window rate limiting backed by Redis — cheap, correct enough for an MVP,
and easy to reason about under audit (StromeX Editorial Bible, Part VIII: reliability)."""

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis


class RateLimiter:
    def __init__(self, times: int, seconds: int, bucket: str) -> None:
        self.times = times
        self.seconds = seconds
        self.bucket = bucket

    def __call__(self, request: Request) -> None:
        client_id = request.client.host if request.client else "unknown"
        user = getattr(request.state, "user_id", None)
        identity = str(user) if user else client_id
        key = f"ratelimit:{self.bucket}:{identity}"

        r = get_redis()
        current = r.incr(key)
        if current == 1:
            r.expire(key, self.seconds)
        if current > self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests — please slow down and try again shortly.",
            )

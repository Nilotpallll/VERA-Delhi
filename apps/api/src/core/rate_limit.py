"""Rate limiting via Redis.

Uses a sliding-window counter per (IP, route) stored in Redis.
When Redis is unavailable, requests are allowed through (fail-open) with a warning log.
Configurable limits per endpoint category.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status

from .config import settings
from .observability import logger
from .redis_client import get_redis_client


class RateLimiter:
    """
    Sliding-window rate limiter backed by Redis.

    Usage as a FastAPI dependency::

        @router.post("/investigations")
        async def create(
            _: None = Depends(RateLimiter(limit=20, window=60)),
        ):
            ...
    """

    def __init__(
        self,
        limit: int | None = None,
        window: int = 60,
        key_prefix: str = "rl",
    ) -> None:
        self.limit = limit or settings.RATE_LIMIT_PER_MINUTE
        self.window = window
        self.key_prefix = key_prefix

    async def __call__(self, request: Request) -> None:
        client_ip = _get_client_ip(request)
        path_slug = request.url.path.replace("/", "_").strip("_") or "root"
        window_start = int(datetime.now(UTC).timestamp()) // self.window
        key = f"{self.key_prefix}:{client_ip}:{path_slug}:{window_start}"

        try:
            redis = get_redis_client()
            count: Any = await redis.incr(key)
            # Set TTL only on first increment
            if int(count) == 1:
                await redis.expire(key, self.window)

            remaining = max(0, self.limit - int(count))
            # Attach rate limit headers to request state for later injection
            request.state.rate_limit_remaining = remaining
            request.state.rate_limit_limit = self.limit

            if int(count) > self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please retry after a short delay.",
                        "limit": self.limit,
                        "window_seconds": self.window,
                        "remaining": 0,
                    },
                    headers={
                        "Retry-After": str(self.window),
                        "X-RateLimit-Limit": str(self.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str((window_start + 1) * self.window),
                    },
                )
        except HTTPException:
            raise
        except Exception as exc:
            # Fail-open: log and continue rather than blocking legitimate traffic
            logger.warning(
                "Rate limit Redis error (fail-open): %s",
                exc,
                extra={"client_ip": client_ip},
            )


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


# ── Pre-built limiters for dependency injection ───────────────────────────────
default_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_PER_MINUTE,
    key_prefix="rl_default",
)
upload_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_UPLOAD_PER_MINUTE,
    key_prefix="rl_upload",
)
investigation_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_INVESTIGATION_PER_MINUTE,
    key_prefix="rl_investigation",
)


def get_rate_limiter(requests_per_minute: int = 60, window_seconds: int = 60) -> RateLimiter:
    """Factory creating a RateLimiter dependency instance."""
    return RateLimiter(limit=requests_per_minute, window=window_seconds)


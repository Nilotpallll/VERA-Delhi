"""Rate limiting via Redis with multi-tier policies.

Supports:
- Per-IP rate limiting
- Per-User rate limiting
- Expensive-operation rate limiting
- Fail-open resilience when Redis is unavailable (logged warning)
- Dynamic Retry-After and rate limit headers
"""

from datetime import UTC, datetime
from typing import Any, Callable, Literal
from fastapi import HTTPException, Request, status

from .config import settings
from .observability import logger
from .redis_client import get_redis_client


RateLimitScope = Literal["ip", "user", "expensive", "custom"]


class RateLimiter:
    """
    Sliding-window rate limiter backed by Redis.

    Supports scoping by client IP, authenticated user ID, or expensive operation.
    """

    def __init__(
        self,
        limit: int | None = None,
        window: int = 60,
        key_prefix: str = "rl",
        scope: RateLimitScope = "ip",
        key_extractor: Callable[[Request], str] | None = None,
    ) -> None:
        self.limit = limit or settings.RATE_LIMIT_PER_MINUTE
        self.window = window
        self.key_prefix = key_prefix
        self.scope = scope
        self.key_extractor = key_extractor

    async def __call__(self, request: Request) -> None:
        # Determine tracking key based on scope
        if self.key_extractor:
            identifier = self.key_extractor(request)
        elif self.scope == "user":
            identifier = _get_user_identifier(request)
        elif self.scope == "expensive":
            identifier = f"expensive:{_get_client_ip(request)}"
        else:
            identifier = _get_client_ip(request)

        path_slug = request.url.path.replace("/", "_").strip("_") or "root"
        window_start = int(datetime.now(UTC).timestamp()) // self.window
        key = f"{self.key_prefix}:{self.scope}:{identifier}:{path_slug}:{window_start}"

        try:
            redis = get_redis_client()
            count: Any = await redis.incr(key)
            if int(count) == 1:
                await redis.expire(key, self.window)

            remaining = max(0, self.limit - int(count))
            request.state.rate_limit_remaining = remaining
            request.state.rate_limit_limit = self.limit

            if int(count) > self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "scope": self.scope,
                        "message": f"Rate limit exceeded for {self.scope}. Please retry after {self.window}s.",
                        "limit": self.limit,
                        "window_seconds": self.window,
                        "remaining": 0,
                    },
                    headers={
                        "Retry-After": str(self.window),
                        "X-RateLimit-Limit": str(self.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str((window_start + 1) * self.window),
                        "X-RateLimit-Scope": self.scope,
                    },
                )
        except HTTPException:
            raise
        except Exception as exc:
            # Fail-open: log and continue rather than blocking legitimate traffic
            logger.warning(
                "Rate limit Redis error (fail-open) for scope %s: %s",
                self.scope,
                exc,
                extra={"identifier": identifier, "scope": self.scope},
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


def _get_user_identifier(request: Request) -> str:
    # 1. State user injected by Auth middleware
    if hasattr(request.state, "user") and request.state.user:
        user_obj = request.state.user
        if isinstance(user_obj, dict):
            return str(user_obj.get("sub") or user_obj.get("id") or "user")
        if hasattr(user_obj, "id"):
            return str(user_obj.id)
    # 2. Authorization header digest
    auth_header = request.headers.get("Authorization")
    if auth_header and len(auth_header) > 15:
        import hashlib
        return f"tok_{hashlib.sha256(auth_header.encode()).hexdigest()[:16]}"
    # 3. Fallback to IP if unauthenticated
    return f"anon_{_get_client_ip(request)}"


# ── Pre-built limiters for dependency injection ───────────────────────────────
default_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_PER_MINUTE,
    key_prefix="rl_default",
    scope="ip",
)
user_rate_limiter = RateLimiter(
    limit=120,
    key_prefix="rl_user",
    scope="user",
)
expensive_op_rate_limiter = RateLimiter(
    limit=10,
    window=60,
    key_prefix="rl_expensive",
    scope="expensive",
)
upload_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_UPLOAD_PER_MINUTE,
    key_prefix="rl_upload",
    scope="ip",
)
investigation_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_INVESTIGATION_PER_MINUTE,
    key_prefix="rl_investigation",
    scope="ip",
)


def get_rate_limiter(
    requests_per_minute: int = 60,
    window_seconds: int = 60,
    scope: RateLimitScope = "ip",
) -> RateLimiter:
    """Factory creating a RateLimiter dependency instance."""
    return RateLimiter(limit=requests_per_minute, window=window_seconds, scope=scope)

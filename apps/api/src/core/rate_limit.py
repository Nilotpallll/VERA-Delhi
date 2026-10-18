"""Rate limiting via Redis with multi-tier policies and production fail-closed semantics.

Supports:
- Per-IP rate limiting
- Per-User rate limiting
- Expensive-operation rate limiting (fails CLOSED in production when Redis is down)
- Local in-process sliding-window fallback for cheap routes when Redis is down
- Dynamic Retry-After and rate limit headers
"""

import collections
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import HTTPException, Request, status

from .config import settings
from .observability import logger
from .redis_client import get_redis_client

RateLimitScope = Literal["ip", "user", "expensive", "custom"]

# List of expensive routes that must fail closed in production when Redis is down
EXPENSIVE_ROUTES = [
    "run-agent",
    "video",
    "audio",
    "apk",
    "image",
    "analyze",
    "upload",
]


def is_expensive_route(path: str) -> bool:
    """Check if the given request path represents an expensive AI/ML/ingestion operation."""
    p = path.lower()
    return any(slug in p for slug in EXPENSIVE_ROUTES)


# In-process local sliding window fallback for cheap routes when Redis is unavailable
_LOCAL_WINDOWS: dict[str, collections.deque] = collections.defaultdict(collections.deque)


def _check_local_rate_limit(key: str, limit: int, window: int) -> tuple[bool, int]:
    now = time.time()
    dq = _LOCAL_WINDOWS[key]
    while dq and dq[0] <= now - window:
        dq.popleft()
    if len(dq) >= limit:
        return False, 0
    dq.append(now)
    return True, limit - len(dq)


class RateLimiter:
    """
    Sliding-window rate limiter backed by Redis.

    In production:
    - If scope == 'expensive' or request path is expensive, and Redis is unreachable -> FAILS CLOSED (HTTP 503).
    - If cheap route and Redis is unreachable -> falls back to local in-process sliding window.
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
        path_slug = request.url.path.replace("/", "_").strip("_") or "root"
        is_expensive = self.scope == "expensive" or is_expensive_route(request.url.path)

        # Determine tracking key based on scope
        if self.key_extractor:
            identifier = self.key_extractor(request)
        elif self.scope == "user":
            identifier = _get_user_identifier(request)
        elif is_expensive:
            identifier = f"expensive:{_get_client_ip(request)}"
        else:
            identifier = _get_client_ip(request)

        # Enforce quota limits and exhaustion policy
        from .quota_tracker import check_quota_or_fail, track_upstash_command_usage
        await check_quota_or_fail(is_expensive=is_expensive)

        window_start = int(datetime.now(UTC).timestamp()) // self.window
        key = f"{self.key_prefix}:{self.scope}:{identifier}:{path_slug}:{window_start}"

        try:
            redis = get_redis_client()
            count: Any = await redis.incr(key)
            if int(count) == 1:
                await redis.expire(key, self.window)
            await track_upstash_command_usage(command_count=2)

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
            # Check production fail-closed invariant
            if settings.is_production and is_expensive:
                logger.error(
                    "Redis rate-limiter unreachable in production for expensive route %s; FAILING CLOSED: %s",
                    request.url.path,
                    exc,
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "service_unavailable",
                        "message": "Service temporarily unavailable. Rate-limiting infrastructure offline.",
                        "route": request.url.path,
                    },
                )

            # For cheap routes when Redis is down, use local in-process sliding window
            allowed, local_remaining = _check_local_rate_limit(f"local:{key}", self.limit, self.window)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "scope": "local_fallback",
                        "message": f"Local rate limit exceeded. Please retry after {self.window}s.",
                        "limit": self.limit,
                    },
                )

            logger.warning(
                "Rate limit Redis error (local fallback applied) for scope %s: %s",
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
    if hasattr(request.state, "user") and request.state.user:
        user_obj = request.state.user
        if isinstance(user_obj, dict):
            return str(user_obj.get("sub") or user_obj.get("id") or "user")
        if hasattr(user_obj, "id"):
            return str(user_obj.id)
    auth_header = request.headers.get("Authorization")
    if auth_header and len(auth_header) > 15:
        import hashlib
        return f"tok_{hashlib.sha256(auth_header.encode()).hexdigest()[:16]}"
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
    scope="expensive",
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

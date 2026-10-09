"""Idempotency key management via Redis.

Clients send ``Idempotency-Key: <uuid>`` to deduplicate mutating requests.
The first response is cached; subsequent identical keys return the cached response.
"""

import json
from typing import Any

from fastapi import HTTPException, Request, status

from .config import settings
from .observability import logger
from .redis_client import get_redis_client

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_KEY_PREFIX = "idempotency:"


async def get_idempotency_key(request: Request) -> str | None:
    """Extract and return the Idempotency-Key header value, or None."""
    return request.headers.get(IDEMPOTENCY_HEADER)


async def check_idempotent_cache(key: str) -> dict | None:
    """
    Look up a cached response for this idempotency key.
    Returns the cached response dict or None if not found.
    """
    redis_key = f"{IDEMPOTENCY_KEY_PREFIX}{key}"
    try:
        redis = get_redis_client()
        raw = await redis.get(redis_key)
        if raw is not None:
            logger.info("Idempotency cache hit", extra={"idempotency_key": key})
            return json.loads(raw)
        return None
    except Exception as exc:
        logger.warning("Idempotency Redis error (cache miss): %s", exc)
        return None


# Alias for compatibility with router handlers
get_idempotency_response = check_idempotent_cache


async def store_idempotent_response(key: str, response_data: Any) -> None:
    """Store a response under the given idempotency key with configured TTL."""
    redis_key = f"{IDEMPOTENCY_KEY_PREFIX}{key}"
    try:
        redis = get_redis_client()
        await redis.set(
            redis_key,
            json.dumps(response_data, default=str),
            ex=settings.IDEMPOTENCY_KEY_TTL,
        )
        logger.info(
            "Idempotency response cached",
            extra={"idempotency_key": key, "ttl": settings.IDEMPOTENCY_KEY_TTL},
        )
    except Exception as exc:
        logger.warning("Failed to cache idempotency response: %s", exc)


# Alias for compatibility with router handlers
store_idempotency_response = store_idempotent_response



def validate_idempotency_key_format(key: str) -> str:
    """Validate that the key is a reasonable UUID-like string."""
    import re
    if not re.match(r"^[a-zA-Z0-9\-_]{8,128}$", key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_idempotency_key",
                "message": (
                    "Idempotency-Key must be 8–128 characters: "
                    "letters, digits, hyphens, or underscores."
                ),
            },
        )
    return key

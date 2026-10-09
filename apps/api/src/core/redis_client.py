"""Redis client for Upstash (HTTP REST API) and local Redis fallback.

Upstash exposes a REST endpoint — no native TCP Redis is needed for serverless.
For local dev, standard Redis is used via the redis-py async client.
"""

import json
from typing import Any

import httpx

from .config import settings
from .observability import logger

# ── Module-level client instances ─────────────────────────────────────────────
_redis_client = None


class UpstashRedisHTTPClient:
    """
    Thin HTTP wrapper around the Upstash Redis REST API.
    Compatible interface with redis-py's basic get/set/delete/exists/expire.
    """

    def __init__(self, url: str, token: str) -> None:
        self._url = url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _call(self, *args: Any) -> Any:
        payload = list(args)
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(self._url, headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result")

    async def get(self, key: str) -> str | None:
        return await self._call("GET", key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        if ex is not None:
            await self._call("SET", key, json.dumps(value), "EX", ex)
        else:
            await self._call("SET", key, json.dumps(value))

    async def delete(self, key: str) -> int:
        return await self._call("DEL", key)

    async def exists(self, key: str) -> int:
        return await self._call("EXISTS", key)

    async def expire(self, key: str, seconds: int) -> int:
        return await self._call("EXPIRE", key, seconds)

    async def incr(self, key: str) -> int:
        return await self._call("INCR", key)

    async def ping(self) -> bool:
        result = await self._call("PING")
        return result == "PONG"

    async def ttl(self, key: str) -> int:
        return await self._call("TTL", key)


class LocalRedisClient:
    """Async redis-py client wrapper for local development."""

    def __init__(self, url: str = "redis://localhost:6379") -> None:
        import redis.asyncio as aioredis
        self._client = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        await self._client.set(key, json.dumps(value), ex=ex)

    async def delete(self, key: str) -> int:
        return await self._client.delete(key)

    async def exists(self, key: str) -> int:
        return await self._client.exists(key)

    async def expire(self, key: str, seconds: int) -> int:
        return await self._client.expire(key, seconds)

    async def incr(self, key: str) -> int:
        return await self._client.incr(key)

    async def ping(self) -> bool:
        return await self._client.ping()

    async def ttl(self, key: str) -> int:
        return await self._client.ttl(key)

    async def aclose(self) -> None:
        await self._client.aclose()


class RedisProxy:
    """Proxy object so callers can use redis_client directly without eager init."""

    def __getattr__(self, name: str) -> Any:
        client = get_redis_client()
        return getattr(client, name)

    async def ping(self) -> bool:
        try:
            client = get_redis_client()
            return await client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        global _redis_client
        if _redis_client is not None:
            if hasattr(_redis_client, "aclose"):
                await _redis_client.aclose()
            elif hasattr(_redis_client, "close"):
                res = _redis_client.close()
                if hasattr(res, "__await__"):
                    await res
            _redis_client = None


redis_client = RedisProxy()


def get_redis_client():
    """Return the configured Redis client (Upstash REST or local redis-py)."""
    global _redis_client
    if _redis_client is None:
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            logger.info("Using Upstash Redis REST client")
            _redis_client = UpstashRedisHTTPClient(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN,
            )
        else:
            logger.info("Upstash not configured; using local Redis (redis://localhost:6379)")
            _redis_client = LocalRedisClient()
    return _redis_client


async def check_redis_health() -> dict[str, str]:
    """Ping Redis and return health status."""
    try:
        client = get_redis_client()
        alive = await client.ping()
        return {"status": "connected" if alive else "degraded"}
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return {"status": "unavailable", "error": str(exc)}


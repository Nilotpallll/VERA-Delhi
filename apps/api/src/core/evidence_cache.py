"""Deterministic Evidence Hash Cache for VERA.

Architecture Rule 13: Deterministic and reproducible.
Caches repeated evidence payloads keyed by cryptographic SHA-256 hash.
Repeated submissions skip expensive rate limit penalties and LLM calls.
"""

import hashlib
import json
import logging
from typing import Any

from .redis_client import get_redis_client

logger = logging.getLogger("vera.core.evidence_cache")

# Default TTL: 24 hours (86,400 seconds)
DEFAULT_CACHE_TTL = 86400

# Local in-process fallback for tests
_LOCAL_EVIDENCE_CACHE: dict[str, dict[str, Any]] = {}


def compute_evidence_hash(evidence_type: str, payload: str, metadata: dict[str, Any] | None = None) -> str:
    """Compute a deterministic SHA-256 hash over evidence attributes."""
    hasher = hashlib.sha256()
    hasher.update(evidence_type.strip().lower().encode("utf-8"))
    hasher.update(b"::")
    hasher.update(payload.strip().encode("utf-8"))
    if metadata:
        meta_str = json.dumps(metadata, sort_keys=True)
        hasher.update(b"::")
        hasher.update(meta_str.encode("utf-8"))
    return hasher.hexdigest()


async def get_cached_evidence_analysis(evidence_hash: str) -> dict[str, Any] | None:
    """Retrieve cached analysis findings if present."""
    cache_key = f"vera:cache:evidence:{evidence_hash}"
    try:
        redis = get_redis_client()
        raw = await redis.get(cache_key)
        if raw:
            logger.info("Evidence cache HIT for %s", evidence_hash[:12])
            return json.loads(raw)
    except Exception as exc:
        logger.debug("Redis evidence cache lookup error: %s", exc)
        # Check local cache for test environment
        if evidence_hash in _LOCAL_EVIDENCE_CACHE:
            return _LOCAL_EVIDENCE_CACHE[evidence_hash]
    return None


async def store_cached_evidence_analysis(
    evidence_hash: str,
    analysis_result: dict[str, Any],
    ttl: int = DEFAULT_CACHE_TTL,
) -> None:
    """Store analysis result keyed by evidence hash."""
    cache_key = f"vera:cache:evidence:{evidence_hash}"
    try:
        redis = get_redis_client()
        await redis.set(cache_key, json.dumps(analysis_result), ex=ttl)
    except Exception as exc:
        logger.debug("Redis evidence cache store error: %s", exc)
        _LOCAL_EVIDENCE_CACHE[evidence_hash] = analysis_result

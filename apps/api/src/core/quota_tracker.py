"""Upstash Free Tier Usage Tracking, Alerting & Exhaustion Enforcer.

Free Tier Budgets:
- Upstash Redis: 500,000 commands/month (~16,666 commands/day)
- Upstash QStash: 1,000 messages/day

Defined behavior at exhaustion:
- Expensive routes (LLM, video, audio, APK, run-agent): HTTP 503 "Capacity reached"
- Cheap routes (read, list, health): Degrade to local in-process sliding window
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from .redis_client import get_redis_client

logger = logging.getLogger("vera.core.quota")

# Daily / Monthly command limits
DAILY_COMMAND_CAP = 16_666
MONTHLY_COMMAND_CAP = 500_000
DAILY_QSTASH_CAP = 1_000

# Estimated command costs per route category
ROUTE_COMMAND_COSTS: dict[str, int] = {
    "cheap_read": 1,        # 1 GET / check
    "mutation": 3,          # Rate limit + session + idempotency
    "expensive": 10,        # Rate limit + cache check + lock + queue publish
}

# Local in-process counters for tests / offline
_LOCAL_DAILY_COUNT = 0
_LOCAL_MONTHLY_COUNT = 0


def get_current_period_keys() -> tuple[str, str]:
    now = datetime.now(UTC)
    day_str = now.strftime("%Y-%m-%d")
    month_str = now.strftime("%Y-%m")
    return f"vera:quota:redis:daily:{day_str}", f"vera:quota:redis:monthly:{month_str}"


async def track_upstash_command_usage(command_count: int = 1) -> dict[str, Any]:
    """Increments Redis command counter and emits alerts at 70% and 90% thresholds."""
    global _LOCAL_DAILY_COUNT, _LOCAL_MONTHLY_COUNT
    daily_key, monthly_key = get_current_period_keys()

    daily_used = _LOCAL_DAILY_COUNT + command_count
    monthly_used = _LOCAL_MONTHLY_COUNT + command_count

    try:
        redis = get_redis_client()
        daily_used = await redis.incrby(daily_key, command_count)
        monthly_used = await redis.incrby(monthly_key, command_count)
        # Ensure TTL is set (2 days for daily, 35 days for monthly)
        await redis.expire(daily_key, 172800)
        await redis.expire(monthly_key, 3024000)
    except Exception as exc:
        logger.debug("Quota tracking in local mode: %s", exc)
        _LOCAL_DAILY_COUNT = daily_used
        _LOCAL_MONTHLY_COUNT = monthly_used

    # Check alert thresholds
    daily_pct = (daily_used / DAILY_COMMAND_CAP) * 100.0
    monthly_pct = (monthly_used / MONTHLY_COMMAND_CAP) * 100.0

    if daily_pct >= 90.0 or monthly_pct >= 90.0:
        logger.error(
            "CRITICAL: Upstash Redis quota at 90%%+ capacity! Daily: %d/%d (%.1f%%), Monthly: %d/%d (%.1f%%)",
            daily_used, DAILY_COMMAND_CAP, daily_pct, monthly_used, MONTHLY_COMMAND_CAP, monthly_pct
        )
    elif daily_pct >= 70.0 or monthly_pct >= 70.0:
        logger.warning(
            "WARNING: Upstash Redis quota at 70%%+ capacity. Daily: %d/%d (%.1f%%)",
            daily_used, DAILY_COMMAND_CAP, daily_pct
        )

    is_exhausted = daily_used >= DAILY_COMMAND_CAP or monthly_used >= MONTHLY_COMMAND_CAP

    return {
        "daily_used": daily_used,
        "daily_cap": DAILY_COMMAND_CAP,
        "daily_pct": round(daily_pct, 1),
        "monthly_used": monthly_used,
        "monthly_cap": MONTHLY_COMMAND_CAP,
        "monthly_pct": round(monthly_pct, 1),
        "is_exhausted": is_exhausted,
    }


async def check_quota_or_fail(is_expensive: bool) -> None:
    """Enforces quota policy. If exhausted: expensive routes fail 503; cheap routes pass."""
    usage = await track_upstash_command_usage(command_count=0)
    if usage["is_exhausted"]:
        if is_expensive:
            logger.error("Rejecting expensive request: Upstash free tier quota exhausted.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "capacity_reached",
                    "message": "Free-tier capacity reached. Heavy forensic operations temporarily throttled.",
                    "quota": usage,
                },
            )
        else:
            logger.warning("Quota exhausted: cheap route degraded to local in-process limiter.")

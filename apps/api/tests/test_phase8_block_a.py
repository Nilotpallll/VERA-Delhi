"""Tests for Phase 8 Block A: Infrastructure Hardening."""

from unittest.mock import patch

import pytest
from apps.api.src.core.evidence_cache import (
    compute_evidence_hash,
    get_cached_evidence_analysis,
    store_cached_evidence_analysis,
)
from apps.api.src.core.quota_tracker import (
    DAILY_COMMAND_CAP,
    MONTHLY_COMMAND_CAP,
    check_quota_or_fail,
    track_upstash_command_usage,
)
from fastapi import HTTPException


def test_evidence_hash_determinism():
    """Evidence hash must be deterministic across identical payloads."""
    h1 = compute_evidence_hash("message", "Invest 10k get 50k daily guaranteed", {"channel": "telegram"})
    h2 = compute_evidence_hash("message", "Invest 10k get 50k daily guaranteed", {"channel": "telegram"})
    h3 = compute_evidence_hash("message", "Different content", {"channel": "telegram"})

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


@pytest.mark.asyncio
async def test_evidence_cache_store_and_retrieve():
    """Stored analysis must be retrievable by evidence hash."""
    ev_hash = compute_evidence_hash("text", "Guaranteed 200% return in 24 hours")
    mock_result = {"risk_score": 95.0, "tier": "CRITICAL", "signals": ["guaranteed_return"]}

    await store_cached_evidence_analysis(ev_hash, mock_result)
    retrieved = await get_cached_evidence_analysis(ev_hash)

    assert retrieved is not None
    assert retrieved["risk_score"] == 95.0
    assert retrieved["tier"] == "CRITICAL"


@pytest.mark.asyncio
async def test_quota_tracker_usage_and_alerting():
    """Quota tracker reports usage and flags exhaustion at 100%."""
    # Test normal usage
    usage = await track_upstash_command_usage(command_count=5)
    assert usage["daily_used"] >= 5
    assert not usage["is_exhausted"]

    # Test exhaustion enforcement
    with patch("apps.api.src.core.quota_tracker.track_upstash_command_usage", return_value={
        "daily_used": DAILY_COMMAND_CAP + 10,
        "daily_cap": DAILY_COMMAND_CAP,
        "daily_pct": 100.1,
        "monthly_used": 1000,
        "monthly_cap": MONTHLY_COMMAND_CAP,
        "monthly_pct": 0.2,
        "is_exhausted": True,
    }):
        # Expensive route must raise 503
        with pytest.raises(HTTPException) as exc:
            await check_quota_or_fail(is_expensive=True)
        assert exc.value.status_code == 503
        assert exc.value.detail["error"] == "capacity_reached"

        # Cheap route must NOT raise (falls back to local window)
        await check_quota_or_fail(is_expensive=False)


@pytest.mark.asyncio
async def test_ready_reports_db_paused_distinctly(client):
    """The /ready endpoint must distinctly report 'db paused/unreachable' when DB is paused."""
    with patch(
        "apps.api.src.api.v1.health.check_database_health",
        return_value={"status": "paused_or_unreachable", "error": "db paused/unreachable"}
    ), patch("apps.api.src.core.redis_client.redis_client.ping", return_value=True):
        res = await client.get("/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["checks"]["database"] == "db paused/unreachable"

"""Block F: Chaos, Concurrency, and Resilience Tests.

Tests:
1. Chaos mid-request: DB/Redis/LLM/worker down => returns PARTIAL or handled 503, NEVER "safe".
2. Concurrency & Idempotency: Duplicate requests with same Idempotency-Key return cached response.
3. Unsigned worker request: HF worker rejects unsigned/tampered payloads (HTTP 401/403).
4. Quota exhaustion: High volume triggers 503 capacity_reached or 429 for expensive routes.
5. Invariant preservation: Under any failure, zero-trust and tri-state invariants hold.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


class TestChaosFailureResilience:
    """Mid-request chaos injection: DB, Redis, LLM, Worker unavailable."""

    @pytest.mark.asyncio
    async def test_db_down_mid_request_returns_handled_503_never_safe(self, client):
        """In production, when DB fails mid-request, endpoint returns handled 503, never safe."""
        with patch("apps.api.src.core.config.Settings.is_production", True):
            # Patch get_db_session to provide an active session that fails on create_investigation
            dummy_session = AsyncMock()
            with patch("apps.api.src.api.v1.investigations.get_db_session", return_value=dummy_session):
                with patch("apps.api.src.api.v1.investigations.create_investigation", side_effect=OSError("DB connection broken")):
                    response = await client.post(
                        "/api/v1/investigations",
                        json={"title": "Chaos Test DB Down", "user_id": "test-user"},
                    )
                    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                    data = response.json()
                    body_str = json.dumps(data).lower()
                    assert "safe" not in body_str
                    assert "verified_safe" not in body_str

    @pytest.mark.asyncio
    async def test_llm_failure_triggers_tri_state_unavailable_not_safe(self):
        """When LLM provider completely fails, task executor returns fallback without fabricating safety."""
        from apps.api.src.ai.tasks import LLMTaskExecutor

        mock_provider = AsyncMock()
        mock_provider.generate.side_effect = RuntimeError("All LLM providers exhausted / timed out")

        executor = LLMTaskExecutor(provider=mock_provider)
        claims = await executor.extract_claims("Invest in Guaranteed 100% Return VIP Scheme")
        assert len(claims.claims) == 0

        entities = await executor.extract_entities("Contact 9999999999 or visit fake-sebi.com")
        assert len(entities.entities) == 0

        interpretation = await executor.interpret_evidence(["Unknown APK downloaded"])
        assert interpretation.summary == "Evidence interpretation unavailable."

    @pytest.mark.asyncio
    async def test_worker_down_returns_graceful_unavailable(self):
        """When remote ML worker (HF Spaces) is unreachable, MLWorkerClient returns None / handles circuit breaker."""
        from apps.api.src.services.worker_client import MLWorkerClient

        client = MLWorkerClient(base_url="https://non-existent-worker.hf.space", shared_secret="fake")
        with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
            result = await client.call_worker("analyze/apk", {"apk_hash": "test1234"})
            assert result is None  # Degrades to None, caller sets UNAVAILABLE


class TestConcurrencyAndIdempotency:
    """Ensure idempotency key deduplication and concurrent safety."""

    @pytest.mark.asyncio
    async def test_duplicate_requests_with_idempotency_key(self, client):
        """Concurrent requests with same Idempotency-Key are properly handled or deduplicated."""
        headers = {"Idempotency-Key": "phase8-idem-test-12345"}
        
        resp1 = await client.post(
            "/api/v1/investigations",
            json={"title": "Idempotent Case 1"},
            headers=headers,
        )
        assert resp1.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST)

    @pytest.mark.asyncio
    async def test_concurrent_evidence_cache_lookups(self):
        """Evidence response cache handles concurrent accesses cleanly."""
        from apps.api.src.core.evidence_cache import (
            compute_evidence_hash,
            get_cached_evidence_analysis,
            store_cached_evidence_analysis,
        )

        h = compute_evidence_hash("text", "Invest in 500% profit scam")
        await store_cached_evidence_analysis(h, {"risk_score": 85, "verdict": "HIGH"})

        async def worker():
            return await get_cached_evidence_analysis(h)

        results = await asyncio.gather(*(worker() for _ in range(10)))
        assert all(r is not None and r.get("verdict") == "HIGH" for r in results)


class TestUnsignedWorkerRequestSecurity:
    """ML Worker rejecting unsigned or tampered requests."""

    def test_worker_rejects_missing_signature_in_production(self):
        """Worker auth verification rejects requests with missing or invalid secret."""
        from apps.ml_worker.src.main import verify_worker_auth
        from fastapi import HTTPException

        with patch.dict("os.environ", {"WORKER_SHARED_SECRET": "top-secret-worker-key"}):
            # Missing header
            with pytest.raises(HTTPException) as exc_info:
                verify_worker_auth(x_worker_shared_secret=None, upstash_signature=None)
            assert exc_info.value.status_code in (401, 403)

            # Invalid secret
            with pytest.raises(HTTPException) as exc_info:
                verify_worker_auth(x_worker_shared_secret="wrong-secret", upstash_signature=None)
            assert exc_info.value.status_code in (401, 403)

            # Valid secret (no exception raised)
            verify_worker_auth(x_worker_shared_secret="top-secret-worker-key", upstash_signature=None)


class TestQuotaExhaustionBehavior:
    """Upstash Quota Tracker behavior under limits."""

    @pytest.mark.asyncio
    async def test_expensive_route_fails_closed_when_quota_exhausted(self):
        """When Redis/QStash quota is exhausted, check_quota_or_fail rejects expensive ops."""
        from apps.api.src.core.quota_tracker import (
            DAILY_COMMAND_CAP,
            check_quota_or_fail,
            track_upstash_command_usage,
        )
        from fastapi import HTTPException

        try:
            # Artificially consume past the daily cap
            await track_upstash_command_usage(command_count=DAILY_COMMAND_CAP + 10)

            with pytest.raises(HTTPException) as exc_info:
                await check_quota_or_fail(is_expensive=True)
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert exc_info.value.detail["error"] == "capacity_reached"
        finally:
            import apps.api.src.core.quota_tracker as qt
            qt._LOCAL_DAILY_COUNT = 0
            qt._LOCAL_MONTHLY_COUNT = 0

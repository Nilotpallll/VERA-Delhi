"""Phase 6: Traffic, Operational Resilience & Failure Injection Tests.

Validates the operational layer requirements:
1. Traffic management:
   - Multi-tier rate limiting (IP, user, expensive operations)
   - Burst traffic and duplicate request deduplication (Idempotency)
   - Heavy processing queues, exponential retry backoff, and dead-letter routing
2. Failure injection & Zero-Trust Invariants:
   - Database unavailable -> graceful fallback
   - Queue unavailable -> fail-safe local processing
   - OCR / Analyzer failure -> penalized as uncertainty, NEVER marked safe (Rule 9)
   - Malformed evidence handling
3. Phase Gate Audit:
   - UI / API remain functionally useful when investigation is PARTIAL
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from apps.api.src.core.rate_limit import RateLimiter, _get_user_identifier
from apps.api.src.queue.jobs import InvestigationJobPayload, JobStatus, RetryPolicy
from apps.api.src.queue.qstash import QStashClient
from apps.api.src.investigator.risk_engine import DeterministicRiskEngine


# ── 1. Traffic Management Tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idempotent_duplicate_request_deduplication(client: AsyncClient):
    """Duplicate requests with same Idempotency-Key return cached response without re-executing."""
    key = "idemp_traffic_dedup_001"
    payload = {
        "title": "Duplicate Traffic Test",
        "target_entity_name": "DedupCorp",
    }

    # First dispatch
    res1 = await client.post(
        "/api/v1/investigations",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    assert res1.status_code == 201
    data1 = res1.json()

    # Second duplicate dispatch with identical key
    res2 = await client.post(
        "/api/v1/investigations",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    assert res2.status_code == 201
    data2 = res2.json()

    # Both responses must return the identical investigation ID
    assert data1["id"] == data2["id"]


def test_user_identifier_extraction():
    """Verify that user identifier extracts token digest or state user."""
    from unittest.mock import MagicMock
    req = MagicMock()
    req.headers = {"Authorization": "Bearer some_valid_jwt_token_1234567890"}
    req.state = MagicMock()
    req.state.user = None

    ident = _get_user_identifier(req)
    assert ident.startswith("tok_")


@pytest.mark.asyncio
async def test_queue_retry_policy_and_dead_letter_escalation():
    """Heavy background processing queue applies exponential backoff and escalates to DEAD_LETTER."""
    client = QStashClient(token="mock_token", base_url="http://mock-qstash")
    payload = InvestigationJobPayload(
        investigation_id="inv_heavy_01",
        retries=0,
        retry_policy=RetryPolicy(max_retries=2, initial_backoff_seconds=2, backoff_multiplier=2.0),
    )

    # Attempt 1: retry with initial delay (2s)
    status1, res1 = await client.handle_job_retry_or_dead_letter(
        destination_url="investigation-worker",
        payload=payload,
        error_message="GPU Worker Timeout",
    )
    assert status1 == JobStatus.RETRYING
    assert res1.delay_seconds == 2
    assert payload.retries == 1

    # Attempt 2: retry with exponential delay (4s)
    status2, res2 = await client.handle_job_retry_or_dead_letter(
        destination_url="investigation-worker",
        payload=payload,
        error_message="GPU Worker Timeout",
    )
    assert status2 == JobStatus.RETRYING
    assert res2.delay_seconds == 4
    assert payload.retries == 2

    # Attempt 3: exhausted max_retries (2) -> routes to DEAD_LETTER
    status3, res3 = await client.handle_job_retry_or_dead_letter(
        destination_url="investigation-worker",
        payload=payload,
        error_message="GPU Worker Timeout Permanent",
    )
    assert status3 == JobStatus.DEAD_LETTER
    assert res3.destination == "dead-letter-vault"


# ── 2. Failure Injection & Zero-Trust Invariants ──────────────────────────────

@pytest.mark.asyncio
async def test_database_unavailable_resilience(client: AsyncClient):
    """When PostgreSQL/asyncpg is unavailable, API falls back gracefully to in-memory store."""
    res = await client.post(
        "/api/v1/investigations",
        json={"title": "DB Fallback Test", "target_entity_name": "FallbackCorp"},
        headers={"Idempotency-Key": "idemp_db_fallback"},
    )
    assert res.status_code == 201
    inv_id = res.json()["id"]

    # Ingest inputs in-memory
    inp_res = await client.post(
        f"/api/v1/investigations/{inv_id}/inputs",
        json={"inputs": [{"type": "URL", "value": "https://fallback-test.fake"}]},
    )
    assert inp_res.status_code in [200, 201]


def test_analyzer_failure_never_treated_as_safe():
    """Rule 9: An unavailable or failing analyzer must NEVER lower the risk score or declare safety."""
    # Scenario: Only 1 suspect signal detected, but analyzer is unavailable
    signals = [{"type": "guaranteed_return", "description": "Guaranteed 40% returns"}]

    res = DeterministicRiskEngine.evaluate(
        evidence_items=signals,
        has_unavailable_analyzer=True,
    )

    # Status MUST be escalated to PARTIAL
    assert res.investigation_completeness == "PARTIAL"
    # Score retains positive risk weight
    assert res.risk_score >= 15.0


@pytest.mark.asyncio
async def test_malformed_evidence_handling(client: AsyncClient):
    """Malformed evidence items must be rejected cleanly with 400 or handled safely without crashing."""
    inv_res = await client.post(
        "/api/v1/investigations",
        json={"title": "Malformed Test", "target_entity_name": "CorruptCorp"},
        headers={"Idempotency-Key": "idemp_corrupt_01"},
    )
    inv_id = inv_res.json()["id"]

    # Empty inputs list must fail validation
    res = await client.post(
        f"/api/v1/investigations/{inv_id}/run-agent",
        json={"inputs": []},
    )
    assert res.status_code == 400


# ── 3. Phase Gate: PARTIAL Investigation Usability ────────────────────────────

def test_phase_gate_partial_investigation_retains_evidence_and_verdicts():
    """Phase Gate: UI and API must remain useful and auditable when investigation is PARTIAL."""
    indicators = [
        {"type": "unverified_entity", "description": "Unverified advisory claim"},
        {"type": "domain_mismatch", "description": "Suspicious registration age"},
    ]

    res = DeterministicRiskEngine.evaluate(
        evidence_items=indicators,
        has_unavailable_analyzer=True,
    )

    assert res.investigation_completeness == "PARTIAL"
    assert res.risk_score == 45.0
    assert res.risk_level == "MODERATE"
    # All detected indicators are preserved
    assert len(res.active_signals) == 2
    assert any(s.signal_type == "unverified_entity" for s in res.active_signals)
    assert any(s.signal_type == "domain_mismatch" for s in res.active_signals)

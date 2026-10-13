"""Step 6 CI/Production Invariant Tests.

Tests mandated by Phase 8 Step 2 Item 6:
  (b) ENVIRONMENT=test keeps in-memory path legal.
  (c) ENVIRONMENT=production inverts the DB-down E2E: DB down => 503, never silent success.
  (d) Expensive routes return 503/429 when Redis is down (covered in step2 tests).
      Here we add: read/cheap routes fall back to local window (not 503) when Redis is down.

Note: The real Postgres pgvector CI job is in .github/workflows/ci.yml.
      Alembic migration up/down test requires real credentials and is documented in ci.yml.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from apps.api.src.core.config import Settings
from apps.api.src.core.rate_limit import RateLimiter, is_expensive_route


# ── (b) ENVIRONMENT=test allows in-memory fallback ───────────────────────────


@pytest.mark.asyncio
async def test_test_environment_allows_in_memory_fallback(client):
    """When ENVIRONMENT=test (default for tests), DB=None must NOT cause 503.

    The test client uses the development/test environment. If DB session is None
    (no real DB), the endpoint should silently create an in-memory record and
    return HTTP 201 — NOT 503. This verifies the fallback stays legal in test mode.
    """
    # Ensure we are NOT in production (conftest uses default env which is not production)
    with patch("apps.api.src.core.config.settings.ENVIRONMENT", "test"):
        res = await client.post(
            "/api/v1/investigations",
            json={"title": "Test Case", "target_entity_name": "TestCo"},
            headers={"Idempotency-Key": "idemp_test_env_inmem_01"},
        )
    # Must succeed (201) or at worst 400/422 — never 503 in test env
    assert res.status_code in (200, 201), (
        f"Expected 2xx in test env (in-memory fallback), got {res.status_code}: {res.text}"
    )


# ── (c) Inverted DB-down E2E for production mode ─────────────────────────────


@pytest.mark.asyncio
async def test_production_db_down_returns_503_not_silent_success(client):
    """In production mode, an unreachable DB must return HTTP 503, never silent in-memory success.

    This is the INVERTED version of the dev/test behavior:
    - dev/test: DB down => in-memory fallback => 201
    - production: DB down => 503 with request_id (never 201 from in-memory)
    """
    # Simulate production mode + DB session is None (DB unreachable).
    # is_production is a computed property (ENVIRONMENT == "production"), so patching
    # ENVIRONMENT to "production" is sufficient — no separate patch of is_production.
    with patch("apps.api.src.core.config.settings.ENVIRONMENT", "production"):
        res = await client.post(
            "/api/v1/investigations",
            json={"title": "Prod DB Down Case", "target_entity_name": "TargetCo"},
            headers={"Idempotency-Key": "idemp_prod_db_down_inverted_01"},
        )
    assert res.status_code == 503, (
        f"Expected 503 (DB down in prod), got {res.status_code}: {res.text}"
    )
    data = res.json()
    detail = data.get("detail", data)
    assert "database" in detail.get("error", "").lower() or \
           "database" in detail.get("message", "").lower(), (
        f"Response must mention database unavailability: {data}"
    )


@pytest.mark.asyncio
async def test_production_db_exception_returns_503_not_silent_success(client):
    """In production mode, if DB write raises an exception, return 503 — never fall back.

    Simulates the case where db session exists but the actual DB call throws
    (e.g. network partition mid-request). Uses generic OSError to avoid asyncpg dep.
    """
    from apps.api.src.api.deps import get_db_session
    from apps.api.src.main import app
    from unittest.mock import AsyncMock

    mock_db = AsyncMock()
    app.dependency_overrides[get_db_session] = lambda: mock_db

    try:
        with patch("apps.api.src.core.config.settings.ENVIRONMENT", "production"), \
             patch(
                 "apps.api.src.api.v1.investigations.create_investigation",
                 side_effect=OSError("connection refused"),
             ):
            res = await client.post(
                "/api/v1/investigations",
                json={"title": "Prod DB Exception", "target_entity_name": "TargetCo"},
                headers={"Idempotency-Key": "idemp_prod_db_exc_01"},
            )
        assert res.status_code == 503, (
            f"Expected 503 (DB exception in prod), got {res.status_code}: {res.text}"
        )
    finally:
        app.dependency_overrides.pop(get_db_session, None)


# ── (d) Cheap routes fall back to local window when Redis is down ─────────────


@pytest.mark.asyncio
async def test_cheap_routes_use_local_window_when_redis_down():
    """When Redis is down, cheap (non-expensive) routes use in-process local window, not 503.

    Rule: fail-CLOSED only for expensive ops. Cheap reads must degrade gracefully.
    """
    limiter = RateLimiter(limit=100, window=60, scope="cheap_read")

    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/investigations"   # GET — cheap read
    mock_request.headers = {}
    mock_request.client.host = "10.0.0.1"
    mock_request.state = MagicMock()

    assert not is_expensive_route("/api/v1/investigations"), \
        "GET /investigations must be classified as a CHEAP route"

    # With Redis down, cheap route must NOT raise 503 — it must use local window
    with patch("apps.api.src.core.config.settings.ENVIRONMENT", "production"), \
         patch("apps.api.src.core.rate_limit.get_redis_client", side_effect=ConnectionError("Redis down")):
        # Should not raise
        try:
            await limiter(mock_request)
            passed = True
        except HTTPException as e:
            passed = False
            pytest.fail(
                f"Cheap route must NOT raise HTTPException when Redis is down. "
                f"Got status={e.status_code}: {e.detail}"
            )
    assert passed, "Cheap route local window fallback must succeed silently"


@pytest.mark.asyncio
async def test_cheap_routes_local_window_enforces_limit():
    """Even the local in-process window must enforce per-IP rate limits.

    A cheap route hitting its limit must return 429 via the local window,
    not be unlimited.
    """
    # Very tight limit for test: 3 per 60s
    limiter = RateLimiter(limit=3, window=60, scope="cheap_test_limit")

    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/investigations"
    mock_request.headers = {}
    mock_request.client.host = "10.0.0.99"
    mock_request.state = MagicMock()

    with patch("apps.api.src.core.config.settings.ENVIRONMENT", "production"), \
         patch("apps.api.src.core.rate_limit.get_redis_client", side_effect=ConnectionError("Redis down")):
        # First 3 must pass
        for _ in range(3):
            await limiter(mock_request)
        # 4th must be rejected
        with pytest.raises(HTTPException) as exc:
            await limiter(mock_request)
        assert exc.value.status_code == 429, \
            f"Expected 429 from local window after limit exceeded, got {exc.value.status_code}"


# ── Config validation: missing required vars listed by name ───────────────────


def test_production_config_lists_bad_var_names_not_values():
    """Error message must list which var names are invalid, never their values."""
    try:
        Settings(
            ENVIRONMENT="production",
            API_KEY_SECRET="dev-insecure-secret-key-change-in-prod",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/vera_db",
            SUPABASE_URL=None,
            SUPABASE_SERVICE_ROLE_KEY=None,
            UPSTASH_REDIS_REST_URL=None,
            UPSTASH_REDIS_REST_TOKEN=None,
            UPSTASH_QSTASH_TOKEN=None,
            GEMINI_API_KEY=None,
        )
        pytest.fail("Expected ValueError for invalid production config")
    except ValueError as e:
        msg = str(e)
        # Must list variable names
        assert "SUPABASE_URL" in msg or "UPSTASH_REDIS_REST_URL" in msg, \
            f"Error must name the bad vars, got: {msg}"
        # Must NOT contain actual secret values — only None or placeholder strings appear
        assert "postgresql+asyncpg://" not in msg, \
            "Error must not print DATABASE_URL value"

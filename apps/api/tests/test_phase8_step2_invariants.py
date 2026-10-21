"""Step 2 Production Invariants and Hardening Tests.

Validates the strict production requirements:
1. Production boot refusal on empty/placeholder/default credentials.
2. /ready returns HTTP 503 when any core dependency is down.
3. In production, DB down returns handled HTTP 503 with safe generic message and request ID (never in-memory fallback).
4. Rate limiter fails CLOSED (HTTP 503) on expensive routes when Redis is down in production.
"""

from unittest.mock import MagicMock, patch

import pytest
from apps.api.src.core.config import Settings
from apps.api.src.core.rate_limit import RateLimiter
from fastapi import HTTPException
from httpx import AsyncClient


def test_production_config_rejects_missing_credentials():
    """Refuse to boot in production with missing or placeholder credentials."""
    # Attempt to initialize production settings with missing or placeholder keys
    with pytest.raises(ValueError) as excinfo:
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
    err_str = str(excinfo.value)
    assert "Invalid production configuration" in err_str
    assert "SUPABASE_URL" in err_str
    assert "UPSTASH_REDIS_REST_URL" in err_str
    assert "GEMINI_API_KEY" in err_str


@pytest.mark.asyncio
async def test_ready_endpoint_returns_503_when_dependencies_down(client: AsyncClient):
    """The /ready endpoint must return HTTP 503 when core dependencies (DB, Redis, etc.) are unavailable."""
    with patch("apps.api.src.api.v1.health.check_database_health", return_value={"status": "unavailable"}), \
         patch("apps.api.src.api.v1.health.redis_client.ping", return_value=False):
        res = await client.get("/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "not_ready"
        assert "checks" in data
        assert data["checks"]["database"] in ("unavailable", "db paused/unreachable")
        assert data["checks"]["redis"] == "unavailable"


@pytest.mark.asyncio
async def test_expensive_routes_fail_closed_when_redis_down():
    """In production, expensive routes must fail CLOSED (HTTP 503) when Redis is unreachable."""
    limiter = RateLimiter(limit=10, window=60, scope="expensive")

    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/investigations/inv_123/run-agent"
    mock_request.headers = {}
    mock_request.client.host = "192.168.1.1"
    mock_request.state = MagicMock()

    # Simulate Redis connection failure in production environment
    with patch("apps.api.src.core.config.settings.ENVIRONMENT", "production"), \
         patch("apps.api.src.core.rate_limit.get_redis_client", side_effect=ConnectionError("Redis down")):
        with pytest.raises(HTTPException) as exc:
            await limiter(mock_request)
        assert exc.value.status_code == 503
        assert "Service temporarily unavailable" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_production_mode_refuses_in_memory_db_fallback(client: AsyncClient):
    """In production mode, missing DB must return handled HTTP 503, never in-memory fallback."""
    from apps.api.src.api.deps import get_db_session
    from apps.api.src.main import app

    async def _mock_offline_db():
        yield None

    app.dependency_overrides[get_db_session] = _mock_offline_db
    try:
        with patch("apps.api.src.core.config.settings.ENVIRONMENT", "production"):
            res = await client.post(
                "/api/v1/investigations",
                json={"title": "Prod Case", "target_entity_name": "TargetCo"},
                headers={"Idempotency-Key": "idemp_prod_db_test_01"},
            )
            assert res.status_code == 503
            data = res.json()
            assert "Database unavailable" in data["detail"]["message"]
            assert "request_id" in data["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)

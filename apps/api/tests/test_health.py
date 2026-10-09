"""Test health endpoints adhering to versioned API contract."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_and_v1_health_contracts(client: AsyncClient):
    # Test root health
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["api_version"] == "v1"
    assert "components" in data

    # Test versioned v1 health
    resp_v1 = await client.get("/api/v1/health")
    assert resp_v1.status_code == 200
    data_v1 = resp_v1.json()
    assert data_v1["status"] in ("healthy", "degraded")
    assert data_v1["version"] == data["version"]


"""Pytest test fixtures."""

import pytest
from apps.api.src.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def cleanup_database_engine():
    yield
    from apps.api.src.core.database import dispose_engine
    await dispose_engine()


"""Authentication boundary and token tests."""

import pytest
from apps.api.src.core.auth import create_access_token, decode_access_token
from apps.api.src.main import app
from httpx import ASGITransport, AsyncClient


def test_jwt_token_generation_and_decoding():
    token = create_access_token(
        subject="usr_test_123",
        role="investigator",
        expires_minutes=15,
    )
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr_test_123"
    assert payload["role"] == "investigator"


def test_jwt_invalid_token():
    payload = decode_access_token("invalid.token.structure")
    assert payload is None


@pytest.mark.asyncio
async def test_request_id_middleware_header():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert "x-request-id" in res.headers
        assert "x-correlation-id" in res.headers

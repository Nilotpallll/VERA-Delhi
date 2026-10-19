"""Authentication boundary and token tests."""

import pytest
from apps.api.src.core.auth import create_access_token, decode_access_token
from apps.api.src.core.rate_limit import _get_client_ip
from apps.api.src.main import app
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request


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
        res = await ac.get("/")
        assert res.status_code == 200
        assert "x-request-id" in res.headers
        assert "x-correlation-id" in res.headers


@pytest.mark.asyncio
async def test_cors_rejects_unconfigured_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/", headers={"Origin": "https://attacker.example"})

    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers


@pytest.mark.asyncio
async def test_cors_allows_configured_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/", headers={"Origin": "http://localhost:3000"})

    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_cors_allows_vercel_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/", headers={"Origin": "https://vera-delhi.vercel.app"})

    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "https://vera-delhi.vercel.app"


def test_rate_limit_client_ip_ignores_spoofed_forwarding_headers():
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [
            (b"x-forwarded-for", b"203.0.113.10, 198.51.100.20"),
            (b"x-real-ip", b"192.0.2.30"),
        ],
        "client": ("10.0.0.5", 12345),
        "server": ("test", 80),
    }

    assert _get_client_ip(Request(scope)) == "10.0.0.5"

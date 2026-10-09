"""Security, MIME, and Upload Endpoint Tests."""

import pytest
from apps.api.src.core.security import (
    is_safe_url,
    sanitize_storage_path,
    validate_file_bytes,
)
from apps.api.src.main import app
from httpx import ASGITransport, AsyncClient


def test_sanitize_storage_path():
    assert sanitize_storage_path("../../etc/passwd") == "etc/passwd"
    assert sanitize_storage_path("foo/../bar") == "bar"
    assert sanitize_storage_path("///evidence/test.png") == "evidence/test.png"


def test_ssrf_url_guard():
    assert is_safe_url("https://example.com/api") is True
    assert is_safe_url("http://127.0.0.1:8000") is False
    assert is_safe_url("http://localhost/secret") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data") is False
    assert is_safe_url("ftp://example.com") is False


def test_file_validation_valid_png():
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    is_valid, mime, sha256, err = validate_file_bytes(png_bytes, "test.png")
    assert is_valid is True
    assert mime == "image/png"
    assert len(sha256) == 64
    assert err is None


def test_file_validation_disallowed_mime():
    exe_bytes = b"MZ" + b"\x00" * 50
    is_valid, mime, sha256, err = validate_file_bytes(exe_bytes, "virus.exe")
    assert is_valid is False
    assert "Disallowed file extension" in err


@pytest.mark.asyncio
async def test_upload_endpoint_success():
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    files = {"file": ("test.png", png_bytes, "image/png")}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/uploads", files=files)
        assert res.status_code == 201
        data = res.json()
        assert data["mime_type"] == "image/png"
        assert "evidence/" in data["storage_path"]

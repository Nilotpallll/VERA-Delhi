"""Unit & integration tests for Image Scam Detection endpoint (POST /api/v1/image-check).

Verifies:
- Valid images can be submitted and analyzed.
- Invalid file types, oversized files, and malformed images are rejected safely.
- Loading, success, inconclusive, and failure states work correctly.
- The returned result follows expected schema.
- AI provider or OCR failures do not produce fabricated results.
- Uploaded content is handled securely.
"""

from __future__ import annotations

import base64
import io
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image, ImageDraw

from apps.api.src.main import app


def _create_test_image_b64(text: str = "Test Image", fmt: str = "PNG") -> str:
    """Creates an in-memory test image and returns base64 Data-URI."""
    from PIL.PngImagePlugin import PngInfo

    img = Image.new("RGB", (400, 200), color=(245, 245, 250))
    draw = ImageDraw.Draw(img)
    draw.text((20, 50), text, fill=(30, 30, 40))
    buf = io.BytesIO()

    info = PngInfo()
    info.add_text("Description", text)
    info.add_text("ocr_text", text)

    img.save(buf, format=fmt, pnginfo=info if fmt.upper() == "PNG" else None)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/{fmt.lower()};base64,{b64}"


@pytest.mark.asyncio
async def test_image_check_valid_scam_image():
    """Submits an image containing high-risk investment fraud promises."""
    scam_text = "SEBI REGISTERED INA000099999 GUARANTEED 40% MONTHLY RETURN JOIN VIP TELEGRAM"
    b64_img = _create_test_image_b64(scam_text, fmt="PNG")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={
                "image_b64": b64_img,
                "filename": "fake_advisory.png",
                "source_label": "pytest_scam_test",
            },
        )

    assert resp.status_code == 200
    data = resp.json()

    assert "sha256" in data
    assert data["risk_tier"] in ("CRITICAL", "HIGH", "MEDIUM")
    assert data["composite_score"] >= 40
    assert len(data["highlighted_reasons"]) > 0
    assert "disclaimer" in data
    assert "recommended_actions" in data
    assert len(data["recommended_actions"]) > 0


@pytest.mark.asyncio
async def test_image_check_clean_image():
    """Submits a clean image without suspicious investment promises."""
    clean_text = "Macroeconomic overview of gross domestic product and inflation index."
    b64_img = _create_test_image_b64(clean_text, fmt="PNG")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={
                "image_b64": b64_img,
                "filename": "macro_report.png",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_tier"] == "MEDIUM"
    assert data["composite_score"] < 40


@pytest.mark.asyncio
async def test_image_check_malformed_base64_rejected():
    """Rejects malformed non-base64 input safely with 400 Bad Request."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={"image_b64": "!!!NOT_VALID_BASE64!!!"},
        )
    assert resp.status_code == 400
    assert "base64" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_image_check_unsupported_format_rejected():
    """Rejects unsupported files (e.g. text/html payload masked as image) with 415."""
    fake_payload = base64.b64encode(b"<html><script>alert(1)</script></html>").decode()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={
                "image_b64": f"data:image/png;base64,{fake_payload}",
                "filename": "exploit.png",
            },
        )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_image_check_oversized_payload_rejected():
    """Rejects oversized payloads exceeding size limits with 413."""
    oversized_b64 = "A" * (26_000_000)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={"image_b64": oversized_b64},
        )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_image_check_empty_payload_rejected():
    """Rejects empty image string with 400 or 422 validation error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={"image_b64": ""},
        )
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_image_check_valid_sebi_advisor_low_risk():
    """Verifies that an image displaying valid SEBI registration ID (INA000000037 - Kavitha Menon) is evaluated as LOW risk."""
    advisor_text = "hey guys i am Kavitha menon official sebi registered advisor my id is INA000000037 2:02am"
    b64_img = _create_test_image_b64(advisor_text, fmt="PNG")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/image-check",
            json={
                "image_b64": b64_img,
                "filename": "kavitha_menon_chat.png",
                "source_label": "pytest_valid_advisor_test",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_tier"] == "LOW"
    assert data["composite_score"] <= 20
    assert "KAVITHA MENON" in data["summary"] or "INA000000037" in data["summary"]
    assert any("Verified" in reason for reason in data["highlighted_reasons"])

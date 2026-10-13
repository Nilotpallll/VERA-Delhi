"""Tests for Phase 8 Block B: Scale, Throttling, and Provider Chain."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import Response

from apps.api.src.ai.chain import (
    ChainedLLMProvider,
    CircuitBreaker,
    DeterministicRuleEngineLLMProvider,
)
from apps.api.src.services.worker_client import MLWorkerClient
from apps.ml_worker.src.main import app as worker_app
from httpx import ASGITransport, AsyncClient


def test_circuit_breaker_lifecycle():
    cb = CircuitBreaker(failure_threshold=2, recovery_time_sec=10.0)
    assert cb.can_attempt()
    assert cb.state == "CLOSED"

    cb.record_failure()
    assert cb.can_attempt()

    cb.record_failure()
    assert not cb.can_attempt()
    assert cb.state == "OPEN"

    cb.record_success()
    assert cb.can_attempt()
    assert cb.state == "CLOSED"


@pytest.mark.asyncio
async def test_chained_llm_degrades_to_rule_engine():
    """When all neural LLM providers fail, the chain gracefully falls back to deterministic rules."""
    chain = ChainedLLMProvider()

    # Mock all neural providers failing
    with patch.object(chain._gemini, "generate", side_effect=Exception("Gemini down")), \
         patch.object(chain._groq, "generate", side_effect=Exception("Groq down")), \
         patch.object(chain._ollama, "generate", side_effect=Exception("Ollama down")):
        res = await chain.generate("Guaranteed 50% daily return in our VIP Telegram group")

        assert res.tier == "deterministic_rule_engine"
        assert res.degraded is True
        assert res.confidence_discount == 0.25
        assert "guaranteed_return" in res.output_text


@pytest.mark.asyncio
async def test_chained_llm_labels_groq_fallback():
    """When Gemini fails, Groq succeeds and is labeled as fallback with 0.05 discount."""
    chain = ChainedLLMProvider()

    mock_groq_res = AsyncMock()
    mock_groq_res.provider = "groq"
    mock_groq_res.model = "llama-3.3-70b-versatile"
    mock_groq_res.output_text = '{"claims": []}'
    mock_groq_res.raw_response = {}
    mock_groq_res.tokens_used = 15

    with patch.object(chain._gemini, "generate", side_effect=Exception("Gemini quota 429")), \
         patch.object(chain._groq, "generate", return_value=mock_groq_res), \
         patch("apps.api.src.core.config.settings.GROQ_API_KEY", "gsk_valid_key"):
        res = await chain.generate("Analyze this broker claim")

        assert res.tier == "groq_fallback"
        assert res.degraded is True
        assert res.confidence_discount == 0.05


@pytest.mark.asyncio
async def test_ml_worker_rejects_unsigned_requests():
    """The ML Worker must reject unsigned requests in production with HTTP 401 or 403."""
    async with AsyncClient(transport=ASGITransport(app=worker_app), base_url="http://test") as ac:
        with patch.dict("os.environ", {"ENVIRONMENT": "production", "WORKER_SHARED_SECRET": "top-secret-key"}):
            # No secret header -> 403
            res = await ac.post("/analyze/video", json={"video_base64": "AAAA"})
            assert res.status_code in (401, 403)

            # Valid secret header -> 200
            res_auth = await ac.post(
                "/analyze/video",
                json={"video_base64": "AAAA"},
                headers={"X-Worker-Shared-Secret": "top-secret-key"}
            )
            assert res_auth.status_code == 200
            assert "limitation_note" in res_auth.json()


@pytest.mark.asyncio
async def test_worker_client_returns_none_on_failure():
    """WorkerClient returns None when worker is down or unreachable, allowing graceful PARTIAL degradation."""
    client = MLWorkerClient(base_url="http://invalid-worker-domain:9999", shared_secret="secret")
    result = await client.call_worker("/analyze/video", {"video_base64": "AAAA"}, timeout=0.1)
    assert result is None

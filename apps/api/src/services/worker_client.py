"""Resilient HTTP client for offloading heavy ML inference to Hugging Face Spaces Worker.

Invariants:
- Uses timeout (15s) + retry + circuit breaker.
- If worker down or times out: sets component to UNAVAILABLE, never fails investigation or marks safe.
- Investigation degrades cleanly to PARTIAL.
"""

import logging
from typing import Any

import httpx

from ..ai.chain import CircuitBreaker
from ..core.config import settings

logger = logging.getLogger("vera.services.worker_client")


class MLWorkerClient:
    def __init__(self, base_url: str | None = None, shared_secret: str | None = None):
        self.base_url = str(base_url or getattr(settings, "ML_WORKER_URL", "http://localhost:7860") or "http://localhost:7860").rstrip("/")
        self.shared_secret = shared_secret or getattr(settings, "WORKER_SHARED_SECRET", "")
        self.breaker = CircuitBreaker(failure_threshold=3, recovery_time_sec=60.0)

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.shared_secret:
            headers["X-Worker-Shared-Secret"] = self.shared_secret
        return headers

    async def call_worker(self, endpoint: str, payload: dict[str, Any], timeout: float = 15.0) -> dict[str, Any] | None:
        """Call remote ML worker with retry, circuit breaker, and graceful fallback to UNAVAILABLE."""
        if not self.breaker.can_attempt():
            logger.warning("ML Worker circuit breaker is OPEN. Fast-failing endpoint %s", endpoint)
            return None

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload, headers=self.headers)
                    if resp.status_code == 200:
                        self.breaker.record_success()
                        return resp.json()
                    elif resp.status_code in (401, 403):
                        logger.error("ML worker authentication rejected: %s", resp.text)
                        return None
                    else:
                        logger.warning("ML worker returned HTTP %d: %s", resp.status_code, resp.text)
            except Exception as exc:
                logger.warning("ML worker call failed (attempt %d/2): %s", attempt + 1, exc)

        self.breaker.record_failure()
        return None


ml_worker_client = MLWorkerClient()

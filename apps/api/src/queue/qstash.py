"""QStash integration boundary for asynchronous investigation task queuing.

Supports:
- Heavy async processing queues
- Configurable retry policy with exponential backoff
- Dead-letter routing on exhausted retries
- Local mock fallback when QStash is not configured
"""

import httpx

from ..core.config import settings
from ..core.observability import logger
from .jobs import InvestigationJobPayload, JobDispatchResult, JobStatus


class QStashClient:
    def __init__(self, token: str | None = None, base_url: str | None = None):
        self._token = token or getattr(settings, "UPSTASH_QSTASH_TOKEN", None) or getattr(settings, "QSTASH_TOKEN", None)
        base = base_url or getattr(settings, "UPSTASH_QSTASH_URL", None) or getattr(settings, "QSTASH_URL", None) or "https://qstash.upstash.io"
        self._base_url = base.rstrip("/")

    @property
    def is_configured(self) -> bool:
        return bool(self._token and not self._token.startswith("placeholder_"))

    async def publish_job(
        self,
        destination_url: str,
        payload: InvestigationJobPayload,
        delay_seconds: int = 0,
    ) -> JobDispatchResult:
        """Publish an asynchronous job invocation via QStash REST API."""
        if not self.is_configured:
            logger.info("QStash unconfigured or in stub mode; queuing investigation %s locally", payload.investigation_id)
            return JobDispatchResult(
                message_id=f"mock_msg_{payload.investigation_id}",
                destination=destination_url,
                status="MOCK_DISPATCHED",
                delay_seconds=delay_seconds,
            )

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        if delay_seconds > 0:
            headers["Upstash-Delay"] = f"{delay_seconds}s"

        target_endpoint = f"{self._base_url}/v2/publish/{destination_url}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(target_endpoint, content=payload.model_dump_json(), headers=headers)
                res.raise_for_status()
                data = res.json()
                return JobDispatchResult(
                    message_id=data.get("messageId", f"msg_{payload.investigation_id}"),
                    destination=destination_url,
                    status="DISPATCHED",
                    delay_seconds=delay_seconds,
                )
            except Exception as exc:
                logger.error("Failed to publish job to QStash: %s", exc)
                return JobDispatchResult(
                    message_id=f"err_{payload.investigation_id}",
                    destination=destination_url,
                    status=f"FAILED: {exc}",
                    delay_seconds=delay_seconds,
                )

    async def handle_job_retry_or_dead_letter(
        self,
        destination_url: str,
        payload: InvestigationJobPayload,
        error_message: str,
    ) -> tuple[JobStatus, JobDispatchResult]:
        """Process job failure: retry with exponential delay or escalate to DEAD_LETTER."""
        payload.retries += 1
        payload.last_error = error_message

        if payload.retries > payload.retry_policy.max_retries:
            # Exhausted retries -> Route to Dead Letter Vault
            logger.warning(
                "Investigation job %s exhausted max retries (%d). Routing to dead-letter queue.",
                payload.investigation_id,
                payload.retry_policy.max_retries,
            )
            result = await self.publish_job(
                destination_url=payload.retry_policy.dead_letter_destination,
                payload=payload,
                delay_seconds=0,
            )
            return JobStatus.DEAD_LETTER, result

        # Compute exponential backoff delay
        delay_sec = payload.retry_policy.calculate_delay_seconds(payload.retries)
        logger.info(
            "Retrying investigation job %s (attempt %d/%d) after %d seconds.",
            payload.investigation_id,
            payload.retries,
            payload.retry_policy.max_retries,
            delay_sec,
        )
        result = await self.publish_job(
            destination_url=destination_url,
            payload=payload,
            delay_seconds=delay_sec,
        )
        return JobStatus.RETRYING, result


# Module-level singleton
qstash_client = QStashClient()

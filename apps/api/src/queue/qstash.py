"""QStash integration boundary for asynchronous investigation task queuing.

Architecture Rule 15: Upstash QStash free tier handles background scheduling.
"""

import httpx

from ..core.config import settings
from ..core.observability import logger
from .jobs import InvestigationJobPayload, JobDispatchResult


class QStashClient:
    def __init__(self, token: str | None = None, base_url: str | None = None):
        self._token = token or settings.QSTASH_TOKEN
        self._base_url = (base_url or settings.QSTASH_URL).rstrip("/")

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
                )
            except Exception as exc:
                logger.error("Failed to publish job to QStash: %s", exc)
                return JobDispatchResult(
                    message_id=f"err_{payload.investigation_id}",
                    destination=destination_url,
                    status=f"FAILED: {exc}",
                )


# Global instance
qstash_client = QStashClient()

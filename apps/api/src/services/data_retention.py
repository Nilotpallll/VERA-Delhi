"""Data retention and privacy — auto-delete old evidence and investigations.

Architecture Rule: No PII in logs or Sentry.
DPDP Act (India) + GDPR: data minimization, right to erasure, retention limits.

Default retention: 90 days for investigations, 30 days for raw evidence blobs.
Can be overridden via env var RETENTION_DAYS_INVESTIGATIONS / RETENTION_DAYS_EVIDENCE.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from ..core.observability import logger


class DataRetentionService:
    """
    Scheduled cleanup of stale investigations and evidence.

    Designed to run as a background task (e.g., via APScheduler or a cron QStash job).
    All delete operations are logged with counts only — never with IDs/PII.
    """

    def __init__(
        self,
        investigation_retention_days: int = 90,
        evidence_retention_days: int = 30,
    ) -> None:
        self.investigation_retention_days = investigation_retention_days
        self.evidence_retention_days = evidence_retention_days

    async def run_cleanup(self, db_session) -> dict[str, int]:
        """
        Delete investigations and evidence older than the retention window.

        Returns counts of deleted rows — no IDs, no content logged.
        """
        now = datetime.now(UTC)
        inv_cutoff = now - timedelta(days=self.investigation_retention_days)
        ev_cutoff = now - timedelta(days=self.evidence_retention_days)

        deleted_investigations = 0
        deleted_evidence = 0

        try:
            # Only attempt if we have a real DB session
            if db_session is not None:
                from sqlalchemy import delete, text

                # Delete old evidence first (FK constraint order)
                ev_result = await db_session.execute(
                    text(
                        "DELETE FROM evidence WHERE created_at < :cutoff"
                    ),
                    {"cutoff": ev_cutoff},
                )
                deleted_evidence = ev_result.rowcount or 0

                # Delete old investigations
                inv_result = await db_session.execute(
                    text(
                        "DELETE FROM investigations WHERE created_at < :cutoff"
                    ),
                    {"cutoff": inv_cutoff},
                )
                deleted_investigations = inv_result.rowcount or 0

                await db_session.commit()

        except Exception as exc:
            # Never log evidence content or IDs — only the error type
            logger.warning(
                "Data retention cleanup failed: %s",
                type(exc).__name__,
                extra={"retention_error_type": type(exc).__name__},
            )
            return {"deleted_investigations": 0, "deleted_evidence": 0, "error": True}

        logger.info(
            "Data retention cleanup complete: investigations=%d evidence=%d",
            deleted_investigations,
            deleted_evidence,
        )
        return {
            "deleted_investigations": deleted_investigations,
            "deleted_evidence": deleted_evidence,
            "error": False,
        }

    async def delete_user_data(self, user_id: str, db_session) -> dict[str, int]:
        """
        Right-to-erasure: delete all data for a specific user.

        Logs only the count of rows deleted — never the user_id or content.
        GDPR Art 17 / DPDP Act §13.
        """
        deleted_investigations = 0
        deleted_evidence = 0

        try:
            if db_session is not None and user_id:
                from sqlalchemy import text

                ev_result = await db_session.execute(
                    text(
                        "DELETE FROM evidence WHERE investigation_id IN "
                        "(SELECT id FROM investigations WHERE user_id = :uid)"
                    ),
                    {"uid": user_id},
                )
                deleted_evidence = ev_result.rowcount or 0

                inv_result = await db_session.execute(
                    text(
                        "DELETE FROM investigations WHERE user_id = :uid"
                    ),
                    {"uid": user_id},
                )
                deleted_investigations = inv_result.rowcount or 0

                await db_session.commit()

        except Exception as exc:
            logger.warning(
                "User data deletion failed: %s",
                type(exc).__name__,
            )
            return {"deleted_investigations": 0, "deleted_evidence": 0, "error": True}

        # Log count only, never the user_id
        logger.info(
            "User data deletion complete: investigations=%d evidence=%d",
            deleted_investigations,
            deleted_evidence,
        )
        return {
            "deleted_investigations": deleted_investigations,
            "deleted_evidence": deleted_evidence,
            "error": False,
        }


# Module-level singleton
retention_service = DataRetentionService()

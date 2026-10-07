"""Base Analyzer contract and safe execution harness.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
Architecture Rule 12: Every model/analyzer must expose version metadata.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from ..contracts.analyzers import AnalyzerExecutionRecord, AnalyzerMetadata
from ..contracts.evidence import CanonicalEvidenceItem
from ..contracts.verification import AnalyzerExecutionStatus

logger = logging.getLogger("vera.engines")


class BaseAnalyzer(ABC):
    """Abstract base class for all independent detection and verification engines."""

    @property
    @abstractmethod
    def metadata(self) -> AnalyzerMetadata:
        """Expose semver and weights/rules digest (Architecture Rule 12)."""
        pass

    @abstractmethod
    async def _execute(self, evidence: CanonicalEvidenceItem) -> tuple[dict[str, Any], float]:
        """Engine-specific execution logic.

        Returns:
            tuple[findings_dict, uncertainty_float_0_to_1]
        """
        pass

    async def execute(self, evidence: CanonicalEvidenceItem) -> AnalyzerExecutionRecord:
        """Safe harness running analyzer execution with failsafe error trapping.

        Architecture Rule 9: Analyzer failure must never be interpreted as safety.
        If an analyzer crashes or times out, status is marked FAILED and uncertainty
        is pegged at 1.0 (maximum penalty).
        """
        started_at = datetime.now(UTC)
        start_tick = time.perf_counter()

        try:
            findings, uncertainty = await self._execute(evidence)
            duration_ms = (time.perf_counter() - start_tick) * 1000.0

            return AnalyzerExecutionRecord(
                metadata=self.metadata,
                status=AnalyzerExecutionStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                execution_duration_ms=round(duration_ms, 2),
                findings=findings,
                uncertainty=max(0.0, min(1.0, uncertainty)),
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_tick) * 1000.0
            logger.error(
                "Analyzer '%s' failed on evidence item '%s': %s",
                self.metadata.name,
                evidence.id,
                str(exc),
                exc_info=True
            )

            # Rule 9: Analyzer failure is NEVER safety; force maximum uncertainty penalty
            return AnalyzerExecutionRecord(
                metadata=self.metadata,
                status=AnalyzerExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                execution_duration_ms=round(duration_ms, 2),
                error_message=f"Analyzer internal failure: {type(exc).__name__} - {str(exc)}",
                findings={"error": str(exc), "safe_default_applied": False},
                uncertainty=1.0,  # 100% uncertain
            )

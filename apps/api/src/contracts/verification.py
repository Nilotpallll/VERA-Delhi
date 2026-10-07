"""Verification state contracts for VERA backend.

Architecture Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED, and UNAVAILABLE.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class VerificationState(StrEnum):
    """Authoritative verification tri-state."""
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    UNAVAILABLE = "UNAVAILABLE"


class AnalyzerExecutionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    SKIPPED = "SKIPPED"


class VerificationResult(BaseModel):
    state: VerificationState
    source: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    confidence: float = Field(ge=0.0, le=1.0)
    details: str
    raw_response_hash: str | None = None
    has_analyzer_failure: bool = False

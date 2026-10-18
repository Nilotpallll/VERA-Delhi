"""Investigation background job lifecycle and schemas for QStash asynchronous tasks."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


class RetryPolicy(BaseModel):
    max_retries: int = 3
    initial_backoff_seconds: int = 5
    backoff_multiplier: float = 2.0
    dead_letter_destination: str = "dead-letter-vault"

    def calculate_delay_seconds(self, current_attempt: int) -> int:
        """Calculate exponential backoff delay."""
        return int(self.initial_backoff_seconds * (self.backoff_multiplier ** max(0, current_attempt - 1)))


class InvestigationJobPayload(BaseModel):
    investigation_id: str
    job_type: str = "FULL_INVESTIGATION"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retries: int = 0
    max_retries: int = 3
    parameters: dict[str, str] = Field(default_factory=dict)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    last_error: str | None = None


class JobDispatchResult(BaseModel):
    message_id: str
    destination: str
    status: str
    delay_seconds: int = 0
    dispatched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

"""Investigation background job lifecycle and schemas for QStash asynchronous tasks."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class InvestigationJobPayload(BaseModel):
    investigation_id: str
    job_type: str = "FULL_INVESTIGATION"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retries: int = 0
    max_retries: int = 3
    parameters: dict[str, str] = Field(default_factory=dict)


class JobDispatchResult(BaseModel):
    message_id: str
    destination: str
    status: str
    dispatched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

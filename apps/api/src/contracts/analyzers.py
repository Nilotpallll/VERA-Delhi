"""Analyzer metadata and execution record contracts.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 12: Every model/analyzer must expose version metadata.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .verification import AnalyzerExecutionStatus


class AnalyzerMetadata(BaseModel):
    name: str = Field(..., description="Unique engine identifier, e.g. engine.ocr.paddle")
    version: str = Field(..., description="Semantic version of analyzer engine logic")
    weights_or_config_digest: str = Field(..., description="Checksum of model weights/rules")
    provider: str = Field(..., description="Engine provider or sub-system team")


class AnalyzerExecutionRecord(BaseModel):
    metadata: AnalyzerMetadata
    status: AnalyzerExecutionStatus
    started_at: datetime
    completed_at: datetime
    execution_duration_ms: float
    error_message: str | None = None
    findings: dict[str, Any] = Field(default_factory=dict)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)

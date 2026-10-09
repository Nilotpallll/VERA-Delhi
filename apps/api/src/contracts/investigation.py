"""Investigation API contracts — Phase 1 + Phase 2 compatible.

Architecture Rule 1: Frontend communicates only through API contracts.
Architecture Rule 2: API contracts are versioned.
Architecture Rule 13: Every investigation must be reproducible.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from .analyzers import AnalyzerExecutionRecord
from .enums import InvestigationStatus  # Phase 2 canonical status (supersedes Phase 1)
from .evidence import CanonicalEvidenceItem, EvidenceMediaType
from .scoring import DeterministicRiskAssessment


class InitialEvidenceInput(BaseModel):
    media_type: EvidenceMediaType
    content_payload: str | None = None
    source_origin: str
    tags: list[str] = Field(default_factory=list)


class InvestigationCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    target_entity_name: str | None = None
    primary_url: str | None = None
    summary_note: str | None = None
    initial_evidence_items: list[InitialEvidenceInput] = Field(default_factory=list)


class InvestigationManifest(BaseModel):
    investigation_id: str
    created_at: datetime
    engine_semver: str
    scoring_algorithm_version: str
    analyzer_versions: dict[str, str]
    configuration_digest: str
    input_digest: str


class InvestigationResponse(BaseModel):
    """Phase 1 backward-compatible response schema."""
    id: str
    status: InvestigationStatus
    title: str
    target_entity_name: str | None = None
    primary_url: str | None = None
    evidence_count: int = 0
    evidence: list[CanonicalEvidenceItem] = Field(default_factory=list)
    risk_assessment: DeterministicRiskAssessment | None = None
    analyzer_records: list[AnalyzerExecutionRecord] = Field(default_factory=list)
    manifest: InvestigationManifest
    created_at: datetime
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    status: str  # healthy | degraded | unhealthy
    version: str
    api_version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    components: dict[str, str | dict[str, str]]

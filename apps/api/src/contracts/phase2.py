"""Phase 2 canonical schemas for entities, relationships, inputs, claims, risk signals, reports.

Architecture Rule 5: Evidence uses one canonical schema (CanonicalEvidenceItem).
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
Architecture Rule 12: Every model/analyzer must expose version metadata.
Architecture Rule 13: Every investigation must be reproducible.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import (
    ClaimStatus,
    EntityType,
    EvidenceCategory,
    EvidenceSeverity,
    InputType,
    RelationshipType,
    ReportStatus,
    SourceType,
)
from .verification import VerificationResult


# ── User (lightweight — Phase 2 stub, Phase 3 wires Supabase Auth) ────────────
class UserRecord(BaseModel):
    id: str
    email: str | None = None
    display_name: str | None = None
    roles: list[str] = Field(default_factory=lambda: ["investigator"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Investigation Input ───────────────────────────────────────────────────────
class InvestigationInputCreate(BaseModel):
    """Submitted by user; the raw artifact the investigation processes."""
    type: InputType
    value: str = Field(..., description="URL, text, phone number, file path, etc.")
    description: str | None = None
    source_label: str | None = Field(None, description="E.g. 'WhatsApp screenshot'")
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestigationInput(BaseModel):
    id: str
    investigation_id: str
    type: InputType
    value: str
    description: str | None = None
    source_label: str | None = None
    submitted_by: str | None = None  # user_id
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Canonical Evidence Item (Phase 2 extended) ────────────────────────────────
class EvidenceItem(BaseModel):
    """Full Phase 2 canonical evidence schema.

    Architecture Rule 5 — every evidence object is immutable and append-only.
    Architecture Rule 9 — failed analyzers create SYSTEM-sourced evidence items.
    """
    id: str
    investigation_id: str

    # Taxonomy
    type: str = Field(..., description="Evidence subtype, e.g. 'deepfake_detection_result'")
    category: EvidenceCategory
    severity: EvidenceSeverity
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Null when not applicable")

    # Content
    description: str
    source_type: SourceType
    source_reference: str = Field(..., description="input_id, evidence_id, or 'system'")

    # Traceability
    analyzer: str | None = Field(None, description="Analyzer name, e.g. 'engine.ocr.paddle'")
    analyzer_version: str | None = None

    # Immutability
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Entity Graph ──────────────────────────────────────────────────────────────
class Entity(BaseModel):
    id: str
    investigation_id: str
    type: EntityType
    value: str = Field(..., description="Canonical value, e.g. phone number, domain, email")
    display_name: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_evidence_ids: list[str] = Field(default_factory=list)
    source_input_ids: list[str] = Field(default_factory=list)
    verification: VerificationResult | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityRelationship(BaseModel):
    """Typed, traceable relationship between two entities."""
    id: str
    investigation_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: RelationshipType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list, description="Evidence supporting this edge")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Claims ────────────────────────────────────────────────────────────────────
class Claim(BaseModel):
    """A specific claim extracted from inputs/evidence that requires verification.

    Architecture Rule — every claim must be traceable to an input/evidence source.
    """
    id: str
    investigation_id: str
    claim_text: str
    claim_type: str = Field(..., description="E.g. 'sebi_registration', 'return_guarantee'")
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    source_input_ids: list[str] = Field(default_factory=list)
    source_evidence_ids: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    refuting_evidence_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Verification Results ──────────────────────────────────────────────────────
class VerificationResultRecord(BaseModel):
    """Stores individual verification check outcomes."""
    id: str
    investigation_id: str
    entity_id: str | None = None
    claim_id: str | None = None
    checker: str = Field(..., description="E.g. 'sebi_registry', 'mca_check', 'whois'")
    checker_version: str
    result: VerificationResult
    source_type: SourceType
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Risk Signals ──────────────────────────────────────────────────────────────
class RiskSignal(BaseModel):
    """Atomic, traceable risk signal contributing to the final score.

    Architecture Rule 6 — deterministic; Rule 7 — LLM cannot assign final score.
    """
    id: str
    investigation_id: str
    signal_type: str = Field(..., description="E.g. 'unregistered_entity', 'deepfake_detected'")
    severity: EvidenceSeverity
    score_contribution: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    source_evidence_ids: list[str] = Field(default_factory=list)
    source_type: SourceType
    deterministic_rule_id: str
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Model Runs ────────────────────────────────────────────────────────────────
class ModelRun(BaseModel):
    """Records an AI/ML model inference run for reproducibility.

    Architecture Rule 12 — every model must expose version metadata.
    Architecture Rule 13 — investigations must be reproducible.
    """
    id: str
    investigation_id: str
    input_id: str | None = None
    evidence_id: str | None = None
    model_name: str
    model_version: str
    model_weights_digest: str
    provider: str
    prompt_digest: str | None = Field(None, description="SHA256 of prompt, for reproducibility")
    output_summary: str | None = None
    output_raw: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float
    success: bool = True
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Analyzer Runs (extended) ──────────────────────────────────────────────────
class AnalyzerRun(BaseModel):
    """Per-evidence analyzer execution record for audit trail.

    Architecture Rule 4 — detection engines are independent modules.
    Architecture Rule 9 — failures never imply safety.
    """
    id: str
    investigation_id: str
    input_id: str | None = None
    evidence_id: str | None = None
    analyzer_name: str
    analyzer_version: str
    weights_digest: str
    status: str  # SUCCESS | FAILED | TIMED_OUT | SKIPPED
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    findings: dict[str, Any] = Field(default_factory=dict)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    error_message: str | None = None
    # System evidence created on failure (Rule 9 failsafe)
    failure_evidence_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Audit Logs ────────────────────────────────────────────────────────────────
class AuditLog(BaseModel):
    """Immutable audit trail entry."""
    id: str
    investigation_id: str | None = None
    actor_type: str = Field(..., description="'user' | 'system' | 'analyzer'")
    actor_id: str
    action: str = Field(..., description="E.g. 'investigation.created', 'evidence.appended'")
    target_type: str | None = None
    target_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Report ────────────────────────────────────────────────────────────────────
class InvestigationReport(BaseModel):
    """Final forensic report — reconstructible from stored system state.

    Architecture Rule 13: Must be reconstructible from inputs + evidence +
    model_runs + analyzer_runs + verification_results + risk_signals.
    """
    id: str
    investigation_id: str
    status: ReportStatus = ReportStatus.DRAFT

    # Investigation summary
    executive_summary: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_tier: str  # Maps to RiskSeverityTier

    # Entity graph snapshot
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[EntityRelationship] = Field(default_factory=list)

    # Evidence summary
    evidence_count: int = 0
    evidence_ids: list[str] = Field(default_factory=list)

    # Claims and verifications
    claims: list[Claim] = Field(default_factory=list)
    verification_results: list[VerificationResultRecord] = Field(default_factory=list)

    # Risk signals
    risk_signals: list[RiskSignal] = Field(default_factory=list)

    # Reproducibility manifest
    model_run_ids: list[str] = Field(default_factory=list)
    analyzer_run_ids: list[str] = Field(default_factory=list)
    engine_version: str
    scoring_algorithm_version: str

    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = 1


# ── API Request/Response Schemas ──────────────────────────────────────────────
class AddInputRequest(BaseModel):
    inputs: list[InvestigationInputCreate] = Field(..., min_length=1)


class AnalyzeRequest(BaseModel):
    """Triggers the analysis pipeline for an investigation."""
    force_rerun: bool = False
    analyzer_subset: list[str] | None = Field(
        None, description="Restrict to specific analyzers; null = all registered"
    )


class EvidenceListResponse(BaseModel):
    investigation_id: str
    total: int
    evidence: list[EvidenceItem]


class InvestigationDetailResponse(BaseModel):
    """Full investigation detail including all phase 2 objects."""
    id: str
    status: str
    title: str
    target_entity_name: str | None = None
    primary_url: str | None = None
    submitted_by: str | None = None
    summary_note: str | None = None

    inputs: list[InvestigationInput] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[EntityRelationship] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    verification_results: list[VerificationResultRecord] = Field(default_factory=list)
    risk_signals: list[RiskSignal] = Field(default_factory=list)
    model_runs: list[ModelRun] = Field(default_factory=list)
    analyzer_runs: list[AnalyzerRun] = Field(default_factory=list)

    risk_score: float | None = None
    risk_tier: str | None = None
    risk_summary: str | None = None

    manifest: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

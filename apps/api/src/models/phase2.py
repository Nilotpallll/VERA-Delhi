"""Phase 2 SQLAlchemy ORM Models — all 12 canonical tables.

Tables:
  users, investigations, inputs, entities, claims, evidence,
  relationships, verification_results, risk_signals, reports,
  model_runs, analyzer_runs, audit_logs

Architecture Rules enforced:
  Rule 5  — one canonical evidence schema
  Rule 8  — tri-state verification
  Rule 9  — failed analyzers never imply safety
  Rule 10 — no Render local filesystem
  Rule 12 — every model/analyzer exposes version metadata
  Rule 13 — every investigation reproducible
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    pass


# ── Users ─────────────────────────────────────────────────────────────────────
class UserModel(Base):
    """Lightweight user record. Phase 3 wires Supabase Auth JWT."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


# ── Investigations ────────────────────────────────────────────────────────────
class InvestigationModel(Base):
    """Master investigation record with full lifecycle state."""
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(
        String(32), default="QUEUED", index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_entity_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Scores
    risk_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    risk_tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reproducibility manifest (Rule 13)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    inputs: Mapped[list["InputModel"]] = relationship(
        "InputModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    entities: Mapped[list["EntityModel"]] = relationship(
        "EntityModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    relationships_list: Mapped[list["RelationshipModel"]] = relationship(
        "RelationshipModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    claims: Mapped[list["ClaimModel"]] = relationship(
        "ClaimModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    verification_results: Mapped[list["VerificationResultModel"]] = relationship(
        "VerificationResultModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    risk_signals: Mapped[list["RiskSignalModel"]] = relationship(
        "RiskSignalModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    model_runs: Mapped[list["ModelRunModel"]] = relationship(
        "ModelRunModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    analyzer_runs: Mapped[list["AnalyzerRunModel"]] = relationship(
        "AnalyzerRunModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    reports: Mapped[list["ReportModel"]] = relationship(
        "ReportModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        "AuditLogModel", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )


# ── Inputs ────────────────────────────────────────────────────────────────────
class InputModel(Base):
    """Raw inputs submitted to an investigation. Immutable after creation."""
    __tablename__ = "inputs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="inputs"
    )


# ── Evidence (Phase 2 canonical) ──────────────────────────────────────────────
class EvidenceModel(Base):
    """Canonical evidence items — append-only, never overwritten.

    Architecture Rule 5: One canonical schema.
    Architecture Rule 9: Failed analyzers produce SYSTEM evidence.
    """
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Taxonomy
    type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)

    # Content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)

    # Traceability (Rule 12)
    analyzer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    analyzer_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Extra metadata
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Immutability enforcement — no updated_at column (append-only)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="evidence"
    )

    __table_args__ = (
        Index("ix_evidence_inv_type", "investigation_id", "type"),
        Index("ix_evidence_inv_severity", "investigation_id", "severity"),
    )


# ── Entities ──────────────────────────────────────────────────────────────────
class EntityModel(Base):
    """Graph node — extracted forensic entities."""
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Double, default=1.0, nullable=False)
    source_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_input_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    verification_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="entities"
    )

    __table_args__ = (
        UniqueConstraint("investigation_id", "type", "value", name="uq_entity_inv_type_value"),
    )


# ── Relationships (Entity Graph Edges) ────────────────────────────────────────
class RelationshipModel(Base):
    """Typed, traceable graph edge between entities."""
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_entity_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("entities.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_entity_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("entities.id", ondelete="CASCADE"), index=True, nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Double, default=1.0, nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="relationships_list"
    )


# ── Claims ────────────────────────────────────────────────────────────────────
class ClaimModel(Base):
    """A verifiable claim extracted from inputs/evidence.

    Every claim must be traceable to an input or evidence source.
    """
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED", nullable=False, index=True)
    source_input_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    refuting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="claims"
    )


# ── Verification Results ──────────────────────────────────────────────────────
class VerificationResultModel(Base):
    """Stores individual verification check outcomes for entities and claims."""
    __tablename__ = "verification_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    claim_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True, index=True
    )
    checker: Mapped[str] = mapped_column(String(128), nullable=False)
    checker_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Tri-state result (Rule 8)
    verification_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Double, default=0.0, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    raw_response_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    has_analyzer_failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="verification_results"
    )


# ── Risk Signals ──────────────────────────────────────────────────────────────
class RiskSignalModel(Base):
    """Atomic risk signal. Deterministic, traceable (Rules 6, 7)."""
    __tablename__ = "risk_signals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score_contribution: Mapped[float] = mapped_column(Double, nullable=False)
    weight: Mapped[float] = mapped_column(Double, nullable=False)
    source_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    deterministic_rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="risk_signals"
    )


# ── Model Runs ────────────────────────────────────────────────────────────────
class ModelRunModel(Base):
    """AI/ML model inference record for reproducibility (Rules 12, 13)."""
    __tablename__ = "model_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    input_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("inputs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    evidence_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_weights_digest: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Double, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="model_runs"
    )


# ── Analyzer Runs ─────────────────────────────────────────────────────────────
class AnalyzerRunModel(Base):
    """Per-evidence analyzer run record (Rules 4, 9, 12)."""
    __tablename__ = "analyzer_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    input_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("inputs.id", ondelete="SET NULL"), nullable=True
    )
    evidence_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    analyzer_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    analyzer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    weights_digest: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Double, nullable=False)
    findings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Double, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # System evidence created on failure (Rule 9)
    failure_evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="analyzer_runs"
    )


# ── Reports ───────────────────────────────────────────────────────────────────
class ReportModel(Base):
    """Final forensic report — append-only versioned (Rule 13)."""
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[float] = mapped_column(Double, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(32), nullable=False)

    # Snapshot references for reproducibility
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    entity_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    claim_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    risk_signal_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    model_run_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    analyzer_run_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scoring_algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="reports"
    )


# ── Audit Logs ────────────────────────────────────────────────────────────────
class AuditLogModel(Base):
    """Immutable, append-only audit trail for all significant actions."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="audit_logs"
    )

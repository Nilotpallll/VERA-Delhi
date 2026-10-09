"""Investigation Service — Phase 2 business logic.

Encapsulates all investigation CRUD operations, input ingestion, analysis
pipeline orchestration, report generation, and audit logging.

Architecture Rules enforced:
  Rule 5  — append-only evidence, never overwritten
  Rule 6  — deterministic scoring
  Rule 7  — LLMs cannot assign final scores
  Rule 9  — failed analyzers create SYSTEM evidence
  Rule 12 — every analyzer run is recorded with version
  Rule 13 — full reproducibility from stored state
"""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..contracts.enums import (
    EvidenceCategory,
    EvidenceSeverity,
    InvestigationStatus,
    SourceType,
)
from ..contracts.phase2 import (
    AddInputRequest,
    AnalyzeRequest,
    EvidenceItem,
    InvestigationDetailResponse,
    InvestigationInput,
    InvestigationInputCreate,
    InvestigationReport,
)
from ..core.config import settings
from ..core.observability import logger
from ..engines.registry import analyzer_registry
from ..models.phase2 import (
    AuditLogModel,
    AnalyzerRunModel,
    ClaimModel,
    EvidenceModel,
    InputModel,
    InvestigationModel,
    ModelRunModel,
    ReportModel,
    RiskSignalModel,
    UserModel,
    VerificationResultModel,
)
from ..scoring.engine import DeterministicScoringEngine


def _new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _now() -> datetime:
    return datetime.now(UTC)


# ── Audit helper ──────────────────────────────────────────────────────────────
async def _append_audit(
    db: AsyncSession,
    *,
    investigation_id: str | None,
    actor_type: str,
    actor_id: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    log = AuditLogModel(
        id=_new_id("audit"),
        investigation_id=investigation_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        created_at=_now(),
    )
    db.add(log)


# ── Investigation CRUD ────────────────────────────────────────────────────────
async def create_investigation(
    db: AsyncSession,
    *,
    title: str,
    target_entity_name: str | None = None,
    primary_url: str | None = None,
    summary_note: str | None = None,
    submitted_by: str | None = None,
    idempotency_key: str | None = None,
) -> InvestigationModel:
    """Create a new investigation with immutable manifest."""
    investigation_id = _new_id("inv")
    now = _now()

    config_digest = hashlib.sha256(
        f"env={settings.ENVIRONMENT}&ver={settings.VERSION}".encode()
    ).hexdigest()
    input_digest = hashlib.sha256(
        f"{title}|{target_entity_name}|{primary_url}".encode()
    ).hexdigest()

    manifest: dict[str, Any] = {
        "investigation_id": investigation_id,
        "created_at": now.isoformat(),
        "engine_semver": settings.VERSION,
        "scoring_algorithm_version": "scoring.v2.0",
        "analyzer_versions": analyzer_registry.list_versions(),
        "configuration_digest": config_digest,
        "input_digest": input_digest,
        "idempotency_key": idempotency_key,
    }

    inv = InvestigationModel(
        id=investigation_id,
        status=InvestigationStatus.QUEUED.value,
        title=title,
        target_entity_name=target_entity_name,
        primary_url=primary_url,
        summary_note=summary_note,
        submitted_by=submitted_by,
        manifest=manifest,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)

    await _append_audit(
        db,
        investigation_id=investigation_id,
        actor_type="system",
        actor_id=submitted_by or "anonymous",
        action="investigation.created",
        target_type="investigation",
        target_id=investigation_id,
        details={"title": title, "target_entity_name": target_entity_name},
    )

    return inv


async def get_investigation(
    db: AsyncSession, investigation_id: str
) -> InvestigationModel | None:
    result = await db.execute(
        select(InvestigationModel).where(InvestigationModel.id == investigation_id)
    )
    return result.scalar_one_or_none()


# ── Input ingestion ───────────────────────────────────────────────────────────
async def add_inputs(
    db: AsyncSession,
    *,
    investigation_id: str,
    inputs: list[InvestigationInputCreate],
    submitted_by: str | None = None,
) -> list[InputModel]:
    """Append inputs to an investigation. Updates status to RUNNING."""
    added: list[InputModel] = []
    for inp in inputs:
        model = InputModel(
            id=_new_id("inp"),
            investigation_id=investigation_id,
            type=inp.type.value,
            value=inp.value,
            description=inp.description,
            source_label=inp.source_label,
            submitted_by=submitted_by,
            extra_metadata=inp.metadata,
            created_at=_now(),
        )
        db.add(model)
        added.append(model)

    # Transition to RUNNING once inputs arrive
    result = await db.execute(
        select(InvestigationModel).where(InvestigationModel.id == investigation_id)
    )
    inv = result.scalar_one_or_none()
    if inv and inv.status == InvestigationStatus.QUEUED.value:
        inv.status = InvestigationStatus.RUNNING.value
        inv.updated_at = _now()

    await _append_audit(
        db,
        investigation_id=investigation_id,
        actor_type="system",
        actor_id=submitted_by or "anonymous",
        action="inputs.added",
        target_type="input",
        target_id=investigation_id,
        details={"count": len(inputs), "types": [i.type.value for i in inputs]},
    )

    return added


# ── Evidence (append-only) ────────────────────────────────────────────────────
async def append_evidence(
    db: AsyncSession,
    *,
    investigation_id: str,
    type: str,
    category: EvidenceCategory,
    severity: EvidenceSeverity,
    description: str,
    source_type: SourceType,
    source_reference: str,
    confidence: float | None = None,
    analyzer: str | None = None,
    analyzer_version: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> EvidenceModel:
    """Append a canonical evidence item. Never overwrites existing evidence."""
    ev = EvidenceModel(
        id=_new_id("ev"),
        investigation_id=investigation_id,
        type=type,
        category=category.value,
        severity=severity.value,
        confidence=confidence,
        description=description,
        source_type=source_type.value,
        source_reference=source_reference,
        analyzer=analyzer,
        analyzer_version=analyzer_version,
        extra_metadata=metadata or {},
        created_at=_now(),
    )
    db.add(ev)
    return ev


# ── Analysis pipeline (stub — no real AI yet) ─────────────────────────────────
async def run_analysis_pipeline(
    db: AsyncSession,
    *,
    investigation_id: str,
    req: AnalyzeRequest,
) -> InvestigationModel:
    """
    Phase 2 analysis pipeline — deterministic stubs only. No real AI.

    For each input:
      1. Record an AnalyzerRun
      2. Append evidence items (system or deterministic)
      3. On failure → append SYSTEM evidence (Rule 9 failsafe)

    Risk scoring is deterministic (Rules 6, 7).
    """
    result = await db.execute(
        select(InvestigationModel).where(InvestigationModel.id == investigation_id)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise ValueError(f"Investigation {investigation_id!r} not found")

    if inv.status not in (
        InvestigationStatus.QUEUED.value,
        InvestigationStatus.RUNNING.value,
        InvestigationStatus.PARTIAL.value,
    ) and not req.force_rerun:
        # Already completed/failed — skip unless forced
        return inv

    inv.status = InvestigationStatus.RUNNING.value
    inv.updated_at = _now()

    await _append_audit(
        db,
        investigation_id=investigation_id,
        actor_type="system",
        actor_id="analysis_pipeline",
        action="analysis.started",
        details={"force_rerun": req.force_rerun},
    )

    # ── Stub analysis passes ──────────────────────────────────────────────────
    # For each input, run a deterministic URL/text analyzer stub
    inputs_result = await db.execute(
        select(InputModel).where(InputModel.investigation_id == investigation_id)
    )
    inputs = list(inputs_result.scalars().all())

    if not inputs:
        # No inputs → INSUFFICIENT_EVIDENCE (failsafe, Rule 9)
        inv.status = InvestigationStatus.INSUFFICIENT_EVIDENCE.value
        inv.updated_at = _now()
        ev = await append_evidence(
            db,
            investigation_id=investigation_id,
            type="insufficient_evidence_signal",
            category=EvidenceCategory.SYSTEM_EVENT,
            severity=EvidenceSeverity.HIGH,
            description="No inputs submitted for analysis. Investigation cannot be completed.",
            source_type=SourceType.SYSTEM,
            source_reference="system",
            metadata={"rule": "RULE-FAILSAFE-002"},
        )
        await _append_audit(
            db,
            investigation_id=investigation_id,
            actor_type="system",
            actor_id="analysis_pipeline",
            action="analysis.insufficient_evidence",
            target_type="evidence",
            target_id=ev.id,
        )
        return inv

    # Process each input with stub analyzers
    risk_signals_created: list[str] = []
    total_score = 0.0
    signal_count = 0

    for inp in inputs:
        started = _now()

        # Stub: URL analyzer
        if inp.type in ("URL", "DOMAIN", "SOCIAL_PROFILE"):
            try:
                findings: dict[str, Any] = {
                    "url": inp.value,
                    "suspicious_keywords": _check_suspicious_url(inp.value),
                    "stub": True,
                }
                completed = _now()
                dur_ms = max(0.1, (completed - started).total_seconds() * 1000)

                ar = AnalyzerRunModel(
                    id=_new_id("ar"),
                    investigation_id=investigation_id,
                    input_id=inp.id,
                    analyzer_name="engine.url.heuristic",
                    analyzer_version="0.1.0-stub",
                    weights_digest=hashlib.sha256(b"url-stub-v0.1.0").hexdigest(),
                    status="SUCCESS",
                    started_at=started,
                    completed_at=completed,
                    duration_ms=dur_ms,
                    findings=findings,
                    uncertainty=0.3,
                    created_at=_now(),
                )
                db.add(ar)

                suspicious = findings["suspicious_keywords"]
                if suspicious:
                    ev = await append_evidence(
                        db,
                        investigation_id=investigation_id,
                        type="suspicious_url_pattern",
                        category=EvidenceCategory.TECHNICAL,
                        severity=EvidenceSeverity.HIGH,
                        description=f"URL contains suspicious keywords: {suspicious}",
                        source_type=SourceType.DETERMINISTIC_ANALYZER,
                        source_reference=inp.id,
                        confidence=0.85,
                        analyzer="engine.url.heuristic",
                        analyzer_version="0.1.0-stub",
                        metadata={"keywords": suspicious, "url": inp.value},
                    )
                    # Risk signal
                    sig = RiskSignalModel(
                        id=_new_id("sig"),
                        investigation_id=investigation_id,
                        signal_type="suspicious_url",
                        severity="HIGH",
                        score_contribution=60.0,
                        weight=0.35,
                        source_evidence_ids=[ev.id],
                        source_type=SourceType.DETERMINISTIC_ANALYZER.value,
                        deterministic_rule_id="RULE-URL-001",
                        description=f"Suspicious URL pattern detected: {suspicious}",
                        created_at=_now(),
                    )
                    db.add(sig)
                    risk_signals_created.append(sig.id)
                    total_score += 60.0 * 0.35
                    signal_count += 1

            except Exception as exc:
                # Rule 9: failure → SYSTEM evidence, never safety
                logger.error("URL analyzer stub failed: %s", exc, exc_info=True)
                completed = _now()
                dur_ms = max(0.1, (completed - started).total_seconds() * 1000)
                ev = await append_evidence(
                    db,
                    investigation_id=investigation_id,
                    type="analyzer_failure",
                    category=EvidenceCategory.SYSTEM_EVENT,
                    severity=EvidenceSeverity.CRITICAL,
                    description=f"URL analyzer failed: {type(exc).__name__}: {exc}",
                    source_type=SourceType.SYSTEM,
                    source_reference="system",
                    metadata={"rule": "RULE-FAILSAFE-001", "error": str(exc)},
                )
                ar = AnalyzerRunModel(
                    id=_new_id("ar"),
                    investigation_id=investigation_id,
                    input_id=inp.id,
                    analyzer_name="engine.url.heuristic",
                    analyzer_version="0.1.0-stub",
                    weights_digest=hashlib.sha256(b"url-stub-v0.1.0").hexdigest(),
                    status="FAILED",
                    started_at=started,
                    completed_at=completed,
                    duration_ms=dur_ms,
                    findings={"error": str(exc), "safe_default_applied": False},
                    uncertainty=1.0,
                    error_message=str(exc),
                    failure_evidence_id=ev.id,
                    created_at=_now(),
                )
                db.add(ar)
                # Failure incurs uncertainty penalty
                total_score += 15.0
                signal_count += 1

        # Stub: Text/phone/email analyzer
        elif inp.type in ("TEXT", "PHONE_NUMBER", "EMAIL_ADDRESS", "UPI_ID"):
            started = _now()
            findings = {"value": inp.value, "type": inp.type, "stub": True}
            completed = _now()
            dur_ms = max(0.1, (completed - started).total_seconds() * 1000)
            ar = AnalyzerRunModel(
                id=_new_id("ar"),
                investigation_id=investigation_id,
                input_id=inp.id,
                analyzer_name="engine.text.basic",
                analyzer_version="0.1.0-stub",
                weights_digest=hashlib.sha256(b"text-stub-v0.1.0").hexdigest(),
                status="SUCCESS",
                started_at=started,
                completed_at=completed,
                duration_ms=dur_ms,
                findings=findings,
                uncertainty=0.5,
                created_at=_now(),
            )
            db.add(ar)
            ev = await append_evidence(
                db,
                investigation_id=investigation_id,
                type="input_registered",
                category=EvidenceCategory.COMMUNICATION,
                severity=EvidenceSeverity.INFO,
                description=f"Input of type {inp.type} registered for analysis: {inp.value[:100]}",
                source_type=SourceType.DETERMINISTIC_ANALYZER,
                source_reference=inp.id,
                confidence=1.0,
                analyzer="engine.text.basic",
                analyzer_version="0.1.0-stub",
            )

        else:
            # Generic passthrough — record input as INFO evidence
            ev = await append_evidence(
                db,
                investigation_id=investigation_id,
                type="input_registered",
                category=EvidenceCategory.SYSTEM_EVENT,
                severity=EvidenceSeverity.INFO,
                description=f"Input of type {inp.type} received, queued for specialized analysis.",
                source_type=SourceType.SYSTEM,
                source_reference=inp.id,
                metadata={"input_type": inp.type},
            )

    # ── Deterministic final score ─────────────────────────────────────────────
    final_score = round(min(100.0, total_score / max(signal_count, 1)), 1) if signal_count else 20.0
    tier = _score_to_tier(final_score)

    inv.risk_score = final_score
    inv.risk_tier = tier
    inv.risk_summary = (
        f"Deterministic score {final_score}/100 ({tier}). "
        f"Analyzed {len(inputs)} inputs, generated {len(risk_signals_created)} risk signals."
    )
    inv.status = InvestigationStatus.COMPLETED.value
    inv.updated_at = _now()

    await _append_audit(
        db,
        investigation_id=investigation_id,
        actor_type="system",
        actor_id="analysis_pipeline",
        action="analysis.completed",
        details={
            "risk_score": final_score,
            "risk_tier": tier,
            "inputs_analyzed": len(inputs),
        },
    )

    return inv


# ── Report generation ─────────────────────────────────────────────────────────
async def generate_report(
    db: AsyncSession, *, investigation_id: str
) -> ReportModel:
    """Generate final forensic report from stored state (Rule 13)."""
    result = await db.execute(
        select(InvestigationModel).where(InvestigationModel.id == investigation_id)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise ValueError(f"Investigation {investigation_id!r} not found")

    # Collect IDs of all stored sub-records
    ev_ids = [e.id for e in inv.evidence]
    entity_ids = []  # entities would be populated here in Phase 3
    claim_ids = [c.id for c in inv.claims]
    sig_ids = [s.id for s in inv.risk_signals]
    model_run_ids = [m.id for m in inv.model_runs]
    ar_ids = [a.id for a in inv.analyzer_runs]

    report = ReportModel(
        id=_new_id("rpt"),
        investigation_id=investigation_id,
        status="FINAL",
        version=1,
        executive_summary=(
            inv.risk_summary
            or f"Investigation {investigation_id} — analysis completed."
        ),
        risk_score=inv.risk_score or 0.0,
        risk_tier=inv.risk_tier or "INCONCLUSIVE",
        evidence_ids=ev_ids,
        entity_ids=entity_ids,
        claim_ids=claim_ids,
        risk_signal_ids=sig_ids,
        model_run_ids=model_run_ids,
        analyzer_run_ids=ar_ids,
        engine_version=settings.VERSION,
        scoring_algorithm_version="scoring.v2.0",
        generated_at=_now(),
        created_at=_now(),
    )
    db.add(report)

    await _append_audit(
        db,
        investigation_id=investigation_id,
        actor_type="system",
        actor_id="report_generator",
        action="report.generated",
        target_type="report",
        target_id=report.id,
        details={"risk_score": report.risk_score, "risk_tier": report.risk_tier},
    )

    return report


# ── Helpers ───────────────────────────────────────────────────────────────────
_SUSPICIOUS_URL_KEYWORDS = [
    "invest", "profit", "return", "guaranteed", "forex", "trading", "wallet",
    "crypto", "free", "bonus", "withdraw", "mining", "doubler", "earn",
]


def _check_suspicious_url(url: str) -> list[str]:
    url_lower = url.lower()
    return [kw for kw in _SUSPICIOUS_URL_KEYWORDS if kw in url_lower]


def _score_to_tier(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score >= 10:
        return "LOW"
    return "SAFE"

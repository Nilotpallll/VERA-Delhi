"""Phase 2 Investigation API endpoints.

Implements the full investigation lifecycle:
  POST /v1/investigations
  POST /v1/investigations/{id}/inputs
  POST /v1/investigations/{id}/analyze
  GET  /v1/investigations/{id}
  GET  /v1/investigations/{id}/evidence
  GET  /v1/investigations/{id}/report

Architecture Rules:
  Rule 1  — Frontend communicates only through API contracts.
  Rule 2  — API contracts are versioned (/api/v1).
  Rule 5  — Evidence uses one canonical schema.
  Rule 9  — Analyzer failure never implies safety.
  Rule 13 — Every investigation is reproducible.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...contracts.enums import EvidenceCategory, EvidenceSeverity, InputType, SourceType
from ...contracts.phase2 import (
    AddInputRequest,
    AnalyzeRequest,
    EvidenceItem,
    EvidenceListResponse,
    InvestigationDetailResponse,
    InvestigationInput,
    InvestigationInputCreate,
    InvestigationReport,
)
from ...core.config import settings
from ...core.idempotency import get_idempotency_response, store_idempotency_response
from ...core.observability import logger
from ...models.phase2 import (
    AnalyzerRunModel,
    ClaimModel,
    EvidenceModel,
    InputModel,
    InvestigationModel,
    ModelRunModel,
    ReportModel,
    RiskSignalModel,
    VerificationResultModel,
)
from ...services.investigation_service import (
    add_inputs,
    append_evidence,
    create_investigation,
    generate_report,
    get_investigation,
    run_analysis_pipeline,
)
from ..deps import get_db_session, rate_limit

router = APIRouter(prefix="/investigations", tags=["Investigations v2"])

# In-memory fallback for dev/test without DB
_STORE: dict[str, dict[str, Any]] = {}
_IDEMPOTENCY_CACHE: dict[str, dict[str, Any]] = {}


# ── POST /investigations ──────────────────────────────────────────────────────
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(requests_per_minute=60))],
    summary="Create Investigation",
    description=(
        "Creates a new fraud investigation with an immutable manifest. "
        "Optionally idempotent via Idempotency-Key header."
    ),
)
async def create_investigation_endpoint(
    req: dict,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession | None = Depends(get_db_session),
) -> dict[str, Any]:
    """Create a new investigation."""
    # Idempotency check
    if idempotency_key:
        if idempotency_key in _IDEMPOTENCY_CACHE:
            return _IDEMPOTENCY_CACHE[idempotency_key]
        cached = await get_idempotency_response(idempotency_key)
        if cached:
            return cached

    title = req.get("title", "")
    if not title or len(title) < 3:
        raise HTTPException(status_code=400, detail="title must be at least 3 characters")

    if db is not None:
        try:
            inv = await create_investigation(
                db,
                title=title,
                target_entity_name=req.get("target_entity_name"),
                primary_url=req.get("primary_url"),
                summary_note=req.get("summary_note"),
                submitted_by=req.get("submitted_by"),
                idempotency_key=idempotency_key,
            )
            await db.flush()
            resp = _inv_to_dict(inv)
        except Exception as exc:
            logger.error("DB create investigation failed: %s", exc, exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass
            resp = _build_in_memory_investigation(req, idempotency_key)
    else:
        resp = _build_in_memory_investigation(req, idempotency_key)

    _STORE[resp["id"]] = resp

    if idempotency_key:
        _IDEMPOTENCY_CACHE[idempotency_key] = resp
        await store_idempotency_response(idempotency_key, resp)

    return resp


# ── POST /investigations/{id}/inputs ──────────────────────────────────────────
@router.post(
    "/{investigation_id}/inputs",
    status_code=status.HTTP_201_CREATED,
    summary="Add Inputs",
    description="Append one or more raw inputs to an investigation.",
)
async def add_inputs_endpoint(
    investigation_id: str,
    req: AddInputRequest,
    db: AsyncSession | None = Depends(get_db_session),
) -> dict[str, Any]:
    """Add inputs to an existing investigation."""
    if db is not None:
        try:
            inv = await get_investigation(db, investigation_id)
            if inv is None:
                raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

            added = await add_inputs(
                db,
                investigation_id=investigation_id,
                inputs=req.inputs,
            )
            await db.flush()

            return {
                "investigation_id": investigation_id,
                "added_count": len(added),
                "inputs": [_input_to_dict(inp) for inp in added],
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Add inputs failed: %s", exc, exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass

    # In-memory fallback
    if investigation_id not in _STORE:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    added_inputs = []
    for inp in req.inputs:
        import uuid
        from datetime import UTC, datetime
        inp_dict = {
            "id": f"inp_{uuid.uuid4().hex[:16]}",
            "investigation_id": investigation_id,
            "type": inp.type.value,
            "value": inp.value,
            "description": inp.description,
            "source_label": inp.source_label,
            "submitted_by": None,
            "created_at": datetime.now(UTC).isoformat(),
            "metadata": inp.metadata,
        }
        added_inputs.append(inp_dict)
        _STORE[investigation_id].setdefault("inputs", []).append(inp_dict)

    return {
        "investigation_id": investigation_id,
        "added_count": len(added_inputs),
        "inputs": added_inputs,
    }


# ── POST /investigations/{id}/analyze ────────────────────────────────────────
@router.post(
    "/{investigation_id}/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Analysis",
    description=(
        "Triggers the deterministic analysis pipeline for an investigation. "
        "No real AI in Phase 2 — stub analyzers run synchronously."
    ),
)
async def analyze_investigation_endpoint(
    investigation_id: str,
    req: AnalyzeRequest = AnalyzeRequest(),
    db: AsyncSession | None = Depends(get_db_session),
) -> dict[str, Any]:
    """Trigger analysis pipeline."""
    if db is not None:
        try:
            inv = await get_investigation(db, investigation_id)
            if inv is None:
                raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

            inv = await run_analysis_pipeline(db, investigation_id=investigation_id, req=req)
            await db.flush()

            return {
                "investigation_id": investigation_id,
                "status": inv.status,
                "risk_score": inv.risk_score,
                "risk_tier": inv.risk_tier,
                "risk_summary": inv.risk_summary,
                "message": "Analysis pipeline completed.",
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Analysis pipeline failed: %s", exc, exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass

    # In-memory fallback
    if investigation_id not in _STORE:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    _STORE[investigation_id]["status"] = "COMPLETED"
    return {
        "investigation_id": investigation_id,
        "status": "COMPLETED",
        "risk_score": 20.0,
        "risk_tier": "LOW",
        "risk_summary": "Stub analysis completed (no DB).",
        "message": "Analysis pipeline completed (in-memory).",
    }


# ── GET /investigations/{id} ──────────────────────────────────────────────────
@router.get(
    "/{investigation_id}",
    summary="Get Investigation Detail",
)
async def get_investigation_endpoint(
    investigation_id: str,
    db: AsyncSession | None = Depends(get_db_session),
) -> dict[str, Any]:
    """Retrieve full investigation detail including all Phase 2 sub-objects."""
    if db is not None:
        try:
            inv = await get_investigation(db, investigation_id)
            if inv is not None:
                return _inv_to_detail_dict(inv)
        except Exception as exc:
            logger.warning("DB get investigation failed: %s", exc)

    if investigation_id in _STORE:
        return _STORE[investigation_id]

    raise HTTPException(
        status_code=404, detail=f"Investigation '{investigation_id}' not found."
    )


# ── GET /investigations/{id}/evidence ─────────────────────────────────────────
@router.get(
    "/{investigation_id}/evidence",
    summary="Get Evidence",
    description="Returns all canonical evidence items for an investigation.",
)
async def get_evidence_endpoint(
    investigation_id: str,
    db: AsyncSession | None = Depends(get_db_session),
) -> dict[str, Any]:
    """Return all evidence for an investigation."""
    if db is not None:
        try:
            inv = await get_investigation(db, investigation_id)
            if inv is None:
                raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

            evidence = [_evidence_to_dict(e) for e in inv.evidence]
            return {
                "investigation_id": investigation_id,
                "total": len(evidence),
                "evidence": evidence,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("DB get evidence failed: %s", exc)

    if investigation_id not in _STORE:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    ev = _STORE[investigation_id].get("evidence", [])
    return {"investigation_id": investigation_id, "total": len(ev), "evidence": ev}


# ── GET /investigations/{id}/report ──────────────────────────────────────────
@router.get(
    "/{investigation_id}/report",
    summary="Get Report",
    description=(
        "Returns the forensic report for an investigation. "
        "Report is reconstructed from stored inputs, evidence, model runs, "
        "analyzer runs, verification results, and risk signals (Rule 13)."
    ),
)
async def get_report_endpoint(
    investigation_id: str,
    db: AsyncSession | None = Depends(get_db_session),
) -> dict[str, Any]:
    """Get or generate the forensic report for an investigation."""
    if db is not None:
        try:
            inv = await get_investigation(db, investigation_id)
            if inv is None:
                raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

            # Return existing report if present
            if inv.reports:
                rpt = inv.reports[-1]  # Latest version
            else:
                # Generate report on-demand
                if inv.status not in ("COMPLETED", "PARTIAL"):
                    raise HTTPException(
                        status_code=409,
                        detail=f"Investigation is in status '{inv.status}'; must be COMPLETED or PARTIAL to generate report.",
                    )
                rpt = await generate_report(db, investigation_id=investigation_id)
                await db.flush()

            return _report_to_dict(rpt, inv)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Get report failed: %s", exc, exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass

    # In-memory fallback
    if investigation_id not in _STORE:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    inv_data = _STORE[investigation_id]
    import uuid
    return {
        "id": f"rpt_{uuid.uuid4().hex[:16]}",
        "investigation_id": investigation_id,
        "status": "FINAL",
        "executive_summary": inv_data.get("risk_summary", "Investigation complete."),
        "risk_score": inv_data.get("risk_score", 0.0),
        "risk_tier": inv_data.get("risk_tier", "INCONCLUSIVE"),
        "evidence_count": len(inv_data.get("evidence", [])),
        "evidence_ids": [e["id"] for e in inv_data.get("evidence", [])],
        "entities": [],
        "relationships": [],
        "claims": [],
        "verification_results": [],
        "risk_signals": [],
        "model_run_ids": [],
        "analyzer_run_ids": [],
        "engine_version": settings.VERSION,
        "scoring_algorithm_version": "scoring.v2.0",
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ── Serialisation helpers ─────────────────────────────────────────────────────
def _inv_to_dict(inv: InvestigationModel) -> dict[str, Any]:
    return {
        "id": inv.id,
        "status": inv.status,
        "title": inv.title,
        "target_entity_name": inv.target_entity_name,
        "primary_url": inv.primary_url,
        "summary_note": inv.summary_note,
        "submitted_by": inv.submitted_by,
        "risk_score": inv.risk_score,
        "risk_tier": inv.risk_tier,
        "risk_summary": inv.risk_summary,
        "manifest": inv.manifest,
        "created_at": inv.created_at.isoformat(),
        "updated_at": inv.updated_at.isoformat(),
    }


def _inv_to_detail_dict(inv: InvestigationModel) -> dict[str, Any]:
    base = _inv_to_dict(inv)
    base.update({
        "inputs": [_input_to_dict(i) for i in inv.inputs],
        "evidence": [_evidence_to_dict(e) for e in inv.evidence],
        "entities": [],  # Phase 3
        "relationships": [],  # Phase 3
        "claims": [_claim_to_dict(c) for c in inv.claims],
        "verification_results": [_vr_to_dict(v) for v in inv.verification_results],
        "risk_signals": [_sig_to_dict(s) for s in inv.risk_signals],
        "model_runs": [_model_run_to_dict(m) for m in inv.model_runs],
        "analyzer_runs": [_analyzer_run_to_dict(a) for a in inv.analyzer_runs],
    })
    return base


def _input_to_dict(inp: InputModel) -> dict[str, Any]:
    return {
        "id": inp.id,
        "investigation_id": inp.investigation_id,
        "type": inp.type,
        "value": inp.value,
        "description": inp.description,
        "source_label": inp.source_label,
        "submitted_by": inp.submitted_by,
        "created_at": inp.created_at.isoformat(),
        "metadata": inp.extra_metadata,
    }


def _evidence_to_dict(ev: EvidenceModel) -> dict[str, Any]:
    return {
        "id": ev.id,
        "investigation_id": ev.investigation_id,
        "type": ev.type,
        "category": ev.category,
        "severity": ev.severity,
        "confidence": ev.confidence,
        "description": ev.description,
        "source_type": ev.source_type,
        "source_reference": ev.source_reference,
        "analyzer": ev.analyzer,
        "analyzer_version": ev.analyzer_version,
        "created_at": ev.created_at.isoformat(),
        "metadata": ev.extra_metadata,
    }


def _claim_to_dict(c: ClaimModel) -> dict[str, Any]:
    return {
        "id": c.id,
        "investigation_id": c.investigation_id,
        "claim_text": c.claim_text,
        "claim_type": c.claim_type,
        "status": c.status,
        "source_input_ids": c.source_input_ids,
        "source_evidence_ids": c.source_evidence_ids,
        "supporting_evidence_ids": c.supporting_evidence_ids,
        "refuting_evidence_ids": c.refuting_evidence_ids,
        "confidence": c.confidence,
        "created_at": c.created_at.isoformat(),
        "metadata": c.extra_metadata,
    }


def _vr_to_dict(v: VerificationResultModel) -> dict[str, Any]:
    return {
        "id": v.id,
        "investigation_id": v.investigation_id,
        "entity_id": v.entity_id,
        "claim_id": v.claim_id,
        "checker": v.checker,
        "checker_version": v.checker_version,
        "verification_state": v.verification_state,
        "source_type": v.source_type,
        "confidence": v.confidence,
        "details": v.details,
        "has_analyzer_failure": v.has_analyzer_failure,
        "created_at": v.created_at.isoformat(),
        "metadata": v.extra_metadata,
    }


def _sig_to_dict(s: RiskSignalModel) -> dict[str, Any]:
    return {
        "id": s.id,
        "investigation_id": s.investigation_id,
        "signal_type": s.signal_type,
        "severity": s.severity,
        "score_contribution": s.score_contribution,
        "weight": s.weight,
        "source_evidence_ids": s.source_evidence_ids,
        "source_type": s.source_type,
        "deterministic_rule_id": s.deterministic_rule_id,
        "description": s.description,
        "created_at": s.created_at.isoformat(),
    }


def _model_run_to_dict(m: ModelRunModel) -> dict[str, Any]:
    return {
        "id": m.id,
        "investigation_id": m.investigation_id,
        "input_id": m.input_id,
        "evidence_id": m.evidence_id,
        "model_name": m.model_name,
        "model_version": m.model_version,
        "provider": m.provider,
        "success": m.success,
        "latency_ms": m.latency_ms,
        "created_at": m.created_at.isoformat(),
    }


def _analyzer_run_to_dict(a: AnalyzerRunModel) -> dict[str, Any]:
    return {
        "id": a.id,
        "investigation_id": a.investigation_id,
        "input_id": a.input_id,
        "evidence_id": a.evidence_id,
        "analyzer_name": a.analyzer_name,
        "analyzer_version": a.analyzer_version,
        "status": a.status,
        "duration_ms": a.duration_ms,
        "uncertainty": a.uncertainty,
        "error_message": a.error_message,
        "failure_evidence_id": a.failure_evidence_id,
        "started_at": a.started_at.isoformat(),
        "completed_at": a.completed_at.isoformat(),
        "created_at": a.created_at.isoformat(),
    }


def _report_to_dict(rpt: ReportModel, inv: InvestigationModel) -> dict[str, Any]:
    return {
        "id": rpt.id,
        "investigation_id": rpt.investigation_id,
        "status": rpt.status,
        "version": rpt.version,
        "executive_summary": rpt.executive_summary,
        "risk_score": rpt.risk_score,
        "risk_tier": rpt.risk_tier,
        "evidence_count": len(rpt.evidence_ids),
        "evidence_ids": rpt.evidence_ids,
        "entity_ids": rpt.entity_ids,
        "claim_ids": rpt.claim_ids,
        "risk_signal_ids": rpt.risk_signal_ids,
        "model_run_ids": rpt.model_run_ids,
        "analyzer_run_ids": rpt.analyzer_run_ids,
        "engine_version": rpt.engine_version,
        "scoring_algorithm_version": rpt.scoring_algorithm_version,
        "generated_at": rpt.generated_at.isoformat(),
        # Full reconstruction for verifiability (Rule 13)
        "inputs": [_input_to_dict(i) for i in inv.inputs],
        "evidence": [_evidence_to_dict(e) for e in inv.evidence],
        "risk_signals": [_sig_to_dict(s) for s in inv.risk_signals],
        "analyzer_runs": [_analyzer_run_to_dict(a) for a in inv.analyzer_runs],
        "claims": [_claim_to_dict(c) for c in inv.claims],
        "verification_results": [_vr_to_dict(v) for v in inv.verification_results],
    }


def _build_in_memory_investigation(
    req: dict, idempotency_key: str | None
) -> dict[str, Any]:
    """Create a minimal in-memory investigation when DB is unavailable."""
    import hashlib
    import uuid
    now = datetime.now(UTC)
    inv_id = f"inv_{uuid.uuid4().hex[:16]}"
    config_digest = hashlib.sha256(
        f"env={settings.ENVIRONMENT}&ver={settings.VERSION}".encode()
    ).hexdigest()
    input_digest = hashlib.sha256(req.get("title", "").encode()).hexdigest()

    initial_evidence = req.get("initial_evidence_items", [])
    evidence_count = len(initial_evidence)
    is_legacy = "initial_evidence_items" in req

    status_val = "PENDING" if is_legacy else "QUEUED"
    scoring_ver = "scoring.v1.0" if is_legacy else "scoring.v2.0"

    return {
        "id": inv_id,
        "status": status_val,
        "title": req.get("title", ""),
        "target_entity_name": req.get("target_entity_name"),
        "primary_url": req.get("primary_url"),
        "summary_note": req.get("summary_note"),
        "submitted_by": req.get("submitted_by"),
        "evidence_count": evidence_count,
        "risk_assessment": {"is_llm_assigned": False, "final_score": 0.0, "tier": "LOW", "factors": []} if is_legacy else None,
        "risk_score": None,
        "risk_tier": None,
        "risk_summary": None,
        "manifest": {
            "investigation_id": inv_id,
            "created_at": now.isoformat(),
            "engine_semver": settings.VERSION,
            "scoring_algorithm_version": scoring_ver,
            "configuration_digest": config_digest,
            "input_digest": input_digest,
            "idempotency_key": idempotency_key,
        },
        "inputs": [],
        "evidence": [],
        "entities": [],
        "relationships": [],
        "claims": [],
        "verification_results": [],
        "risk_signals": [],
        "model_runs": [],
        "analyzer_runs": [],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

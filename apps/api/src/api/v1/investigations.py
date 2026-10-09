"""Investigation management endpoints adhering strictly to versioned contracts.

Supports both SQLAlchemy database persistence and fast fallback.
Architecture Rule 1: Frontend communicates only through API contracts.
Architecture Rule 2: API contracts are versioned.
Architecture Rule 13: Every investigation must be reproducible from stored versions/configuration.
"""

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...contracts.evidence import CanonicalEvidenceItem
from ...contracts.investigation import (
    InvestigationCreateRequest,
    InvestigationManifest,
    InvestigationResponse,
    InvestigationStatus,
)
from ...contracts.scoring import DeterministicRiskAssessment, RiskSeverityTier
from ...contracts.verification import VerificationResult, VerificationState
from ...core.config import settings
from ...core.idempotency import get_idempotency_response, store_idempotency_response
from ...engines.registry import analyzer_registry
from ...models.evidence import EvidenceModel
from ...models.investigation import InvestigationModel
from ..deps import get_db_session, rate_limit

router = APIRouter(prefix="/investigations", tags=["Investigations"])

# In-memory store fallback when DB is not actively running (e.g. initial dev/tests)
_STORE: dict[str, InvestigationResponse] = {}


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(requests_per_minute=60))],
)
async def create_investigation(
    req: InvestigationCreateRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession | None = Depends(get_db_session),
) -> InvestigationResponse:
    """Create a new fraud investigation with immutable manifest and optional idempotency key."""
    # Check idempotency key if provided
    if idempotency_key:
        cached = await get_idempotency_response(idempotency_key)
        if cached:
            return InvestigationResponse.model_validate(cached)

    investigation_id = f"inv_{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC)

    # Compile initial evidence items into CanonicalEvidenceItem
    evidence_list: list[CanonicalEvidenceItem] = []
    for idx, item in enumerate(req.initial_evidence_items):
        payload_bytes = (item.content_payload or "").encode("utf-8")
        evidence_list.append(
            CanonicalEvidenceItem(
                id=f"ev_{uuid.uuid4().hex[:8]}",
                investigation_id=investigation_id,
                media_type=item.media_type,
                sha256=hashlib.sha256(payload_bytes).hexdigest(),
                title=f"Evidence #{idx + 1} ({item.media_type.value})",
                source_origin=item.source_origin,
                content_payload=item.content_payload,
                verification=VerificationResult(
                    state=VerificationState.UNAVAILABLE,
                    source="unprocessed",
                    confidence=0.0,
                    details="Awaiting analyzer pipeline dispatch",
                    has_analyzer_failure=False,
                ),
                created_at=now,
                tags=item.tags,
            )
        )

    # Generate Manifest for Reproducibility (Architecture Rule 13)
    config_digest = hashlib.sha256(f"env={settings.ENVIRONMENT}&ver={settings.VERSION}".encode()).hexdigest()
    input_digest = hashlib.sha256(req.model_dump_json().encode()).hexdigest()

    manifest = InvestigationManifest(
        investigation_id=investigation_id,
        created_at=now,
        engine_semver=settings.VERSION,
        scoring_algorithm_version="scoring.v1.0",
        analyzer_versions=analyzer_registry.list_versions(),
        configuration_digest=config_digest,
        input_digest=input_digest,
    )

    risk = DeterministicRiskAssessment(
        final_score=0.0,
        tier=RiskSeverityTier.SAFE,
        factors=[],
        uncertainty_penalty=0.0,
        algorithm_version="scoring.v1.0",
        summary="Investigation created. Pending inspection.",
        is_llm_assigned=False,
    )

    response = InvestigationResponse(
        id=investigation_id,
        status=InvestigationStatus.PENDING,
        title=req.title,
        target_entity_name=req.target_entity_name,
        primary_url=req.primary_url,
        evidence_count=len(evidence_list),
        evidence=evidence_list,
        risk_assessment=risk,
        analyzer_records=[],
        manifest=manifest,
        created_at=now,
        updated_at=now,
    )

    # Persist to database if available, otherwise in-memory
    if db is not None:
        try:
            inv_model = InvestigationModel(
                id=investigation_id,
                status=InvestigationStatus.PENDING.value,
                title=req.title,
                target_entity_name=req.target_entity_name,
                primary_url=req.primary_url,
                summary_note=req.summary_note,
                evidence_count=len(evidence_list),
                risk_assessment=risk.model_dump(),
                analyzer_records=[],
                manifest=manifest.model_dump(),
                created_at=now,
                updated_at=now,
            )
            for ev in evidence_list:
                ev_model = EvidenceModel(
                    id=ev.id,
                    investigation_id=investigation_id,
                    media_type=ev.media_type.value,
                    sha256=ev.sha256,
                    title=ev.title,
                    source_origin=ev.source_origin,
                    storage_ref=ev.storage_ref.model_dump() if ev.storage_ref else None,
                    content_payload=ev.content_payload,
                    extracted_entities=ev.extracted_entities,
                    verification=ev.verification.model_dump(),
                    tags=ev.tags,
                    created_at=ev.created_at,
                )
                inv_model.evidence.append(ev_model)
            db.add(inv_model)
            await db.flush()
        except Exception:
            # Roll back so the session dependency doesn't error during commit
            try:
                if db.is_active:
                    await db.rollback()
            except Exception:
                pass
            # Fall back to in-memory store seamlessly


    _STORE[investigation_id] = response

    # Cache idempotency key if requested
    if idempotency_key:
        await store_idempotency_response(idempotency_key, response.model_dump(mode="json"))

    return response


@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str,
    db: AsyncSession | None = Depends(get_db_session),
) -> InvestigationResponse:
    """Retrieve investigation by ID from database or memory cache."""
    if db is not None:
        try:
            result = await db.execute(
                select(InvestigationModel).where(InvestigationModel.id == investigation_id)
            )
            inv_model = result.scalar_one_or_none()
            if inv_model:
                evidence = [
                    CanonicalEvidenceItem(
                        id=ev.id,
                        investigation_id=ev.investigation_id,
                        media_type=ev.media_type,
                        sha256=ev.sha256,
                        title=ev.title,
                        source_origin=ev.source_origin,
                        storage_ref=ev.storage_ref,
                        content_payload=ev.content_payload,
                        extracted_entities=ev.extracted_entities,
                        verification=ev.verification,
                        created_at=ev.created_at,
                        tags=ev.tags,
                    )
                    for ev in inv_model.evidence
                ]
                return InvestigationResponse(
                    id=inv_model.id,
                    status=InvestigationStatus(inv_model.status),
                    title=inv_model.title,
                    target_entity_name=inv_model.target_entity_name,
                    primary_url=inv_model.primary_url,
                    evidence_count=inv_model.evidence_count,
                    evidence=evidence,
                    risk_assessment=DeterministicRiskAssessment.model_validate(inv_model.risk_assessment)
                    if inv_model.risk_assessment
                    else None,
                    analyzer_records=inv_model.analyzer_records,
                    manifest=InvestigationManifest.model_validate(inv_model.manifest),
                    created_at=inv_model.created_at,
                    updated_at=inv_model.updated_at,
                )
        except Exception:
            pass

    if investigation_id in _STORE:
        return _STORE[investigation_id]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Investigation '{investigation_id}' not found.",
    )

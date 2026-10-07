"""Investigation management endpoints adhering strictly to versioned contracts.

Architecture Rule 1: Frontend communicates only through API contracts.
Architecture Rule 2: API contracts are versioned.
Architecture Rule 13: Every investigation must be reproducible from stored versions/configuration.
"""

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

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
from ...engines.registry import analyzer_registry

router = APIRouter(prefix="/investigations", tags=["Investigations"])

# In-memory storage for Phase 0 scaffolding before database migration execution
_STORE: dict[str, InvestigationResponse] = {}


@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation(req: InvestigationCreateRequest) -> InvestigationResponse:
    """Create a new fraud investigation with immutable manifest."""
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

    response = InvestigationResponse(
        id=investigation_id,
        status=InvestigationStatus.PENDING,
        title=req.title,
        target_entity_name=req.target_entity_name,
        primary_url=req.primary_url,
        evidence_count=len(evidence_list),
        evidence=evidence_list,
        risk_assessment=DeterministicRiskAssessment(
            final_score=0.0,
            tier=RiskSeverityTier.SAFE,
            factors=[],
            uncertainty_penalty=0.0,
            algorithm_version="scoring.v1.0",
            summary="Investigation created. Pending inspection.",
            is_llm_assigned=False,
        ),
        analyzer_records=[],
        manifest=manifest,
        created_at=now,
        updated_at=now,
    )

    _STORE[investigation_id] = response
    return response


@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(investigation_id: str) -> InvestigationResponse:
    """Retrieve investigation by ID."""
    if investigation_id not in _STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return _STORE[investigation_id]

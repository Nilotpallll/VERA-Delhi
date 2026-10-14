"""Deepfake / media forensics quick-check endpoint.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
Architecture Rule 12: Every model/analyzer exposes version metadata.

POST /api/v1/deepfake-check
  Body: { "video_b64": "<base64-encoded video bytes>" }
  Returns a JSON analysis result with the MesoNet deepfake score.
"""

import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger("vera.api.deepfake")

router = APIRouter(prefix="/deepfake-check", tags=["Deepfake Analysis"])


class DeepfakeCheckRequest(BaseModel):
    """Request body for deepfake quick-check."""

    video_b64: str = Field(
        ...,
        description="Base64-encoded video bytes (may include data-URI prefix).",
    )
    source_label: Optional[str] = Field(
        default="anonymous_upload",
        description="Optional label for audit log.",
    )


class FrameAnalysis(BaseModel):
    frame_index: int
    manipulation_probability: float


class DeepfakeCheckResponse(BaseModel):
    """Response schema for deepfake quick-check."""

    sha256: str
    frames_analyzed: int
    faces_detected: int
    frame_scores: list[float]
    temporal_aggregate_score: float
    temporal_flicker_score: float
    facial_manipulation_signals_detected: bool
    statement: str
    risk_tier: str
    model_version: str
    weights_digest: str
    uncertainty: float


@router.post(
    "",
    response_model=DeepfakeCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Deepfake / Facial Manipulation Quick Check",
    description=(
        "Accepts a base64-encoded video (any container supported by OpenCV / FFmpeg on the server). "
        "Runs the MesoNet-4 spatiotemporal deepfake analysis pipeline and returns per-frame scores, "
        "a temporal aggregate, and the mandatory forensic statement."
    ),
)
async def deepfake_check(body: DeepfakeCheckRequest) -> DeepfakeCheckResponse:
    """Run MesoNet deepfake analysis on a base64-encoded video."""

    # ── Import engine ───────────────────────────────────────────────────────────
    try:
        from ...engines.video_analyzer import VideoAnalyzer
        from ...contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
        from ...contracts.verification import VerificationResult, VerificationState
    except ImportError as exc:
        logger.error("VideoAnalyzer or contracts not importable: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deepfake engine unavailable. Please try again later.",
        )

    raw_b64 = body.video_b64.strip()
    if not raw_b64:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="video_b64 must not be empty.",
        )

    # Strip data-URI prefix if present (browser FileReader produces these)
    if "," in raw_b64 and raw_b64.startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]

    # Decode to bytes for SHA-256 checksum
    try:
        import base64
        video_bytes = base64.b64decode(raw_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid base64 encoding.",
        )

    sha256 = hashlib.sha256(video_bytes).hexdigest()

    # Guard: 50 MB max
    if len(video_bytes) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video too large ({len(video_bytes) // (1024*1024)} MB). Maximum is 50 MB.",
        )

    # ── Build canonical evidence item ──────────────────────────────────────────
    canonical = CanonicalEvidenceItem(
        id=f"ev_df_{sha256[:12]}",
        investigation_id="quick_check",
        media_type=EvidenceMediaType.VIDEO,
        sha256=sha256,
        title="Deepfake Quick Check Upload",
        source_origin=body.source_label or "anonymous_upload",
        content_payload=raw_b64,   # VideoAnalyzer._execute expects the base64 string
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="api_upload",
            confidence=1.0,
            details="Direct deepfake check upload",
        ),
    )

    # ── Run MesoNet engine ─────────────────────────────────────────────────────
    try:
        analyzer = VideoAnalyzer()
        record = await analyzer.execute(evidence=canonical)
    except Exception as exc:
        logger.error("VideoAnalyzer.execute failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(exc)}",
        )

    findings = record.findings or {}

    agg = findings.get("temporal_aggregate_score", 0.0)
    flicker = findings.get("temporal_flicker_score", 0.0)
    frames_analyzed = findings.get("frames_analyzed", 0)
    faces_detected = findings.get("faces_detected", 0)
    frame_scores = findings.get("frame_scores", [])
    has_signals = findings.get("facial_manipulation_signals_detected", False)
    statement = findings.get(
        "statement",
        VideoAnalyzer.MANDATORY_SIGNAL_DESCRIPTION
        if has_signals
        else "No significant signals of facial manipulation detected.",
    )

    # Map score to human-readable risk tier
    if agg >= 0.80:
        risk_tier = "CRITICAL"
    elif agg >= 0.60:
        risk_tier = "HIGH"
    elif agg >= 0.40:
        risk_tier = "MEDIUM"
    elif agg >= 0.20:
        risk_tier = "LOW"
    else:
        risk_tier = "MINIMAL"

    return DeepfakeCheckResponse(
        sha256=sha256,
        frames_analyzed=frames_analyzed,
        faces_detected=faces_detected,
        frame_scores=frame_scores,
        temporal_aggregate_score=round(agg, 4),
        temporal_flicker_score=round(flicker, 4),
        facial_manipulation_signals_detected=has_signals,
        statement=statement,
        risk_tier=risk_tier,
        model_version=analyzer.metadata.version,
        weights_digest=analyzer.metadata.weights_or_config_digest,
        uncertainty=round(record.uncertainty, 4),
    )

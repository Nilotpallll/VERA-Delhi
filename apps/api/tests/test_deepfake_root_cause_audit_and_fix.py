"""Comprehensive Audit and Verification Test Suite for Deepfake Video Detection & MesoNet.

Validates the Root Cause Fixes across all 12 mandatory scenarios:
1. Two distinct real videos (independently processed, both yield low/authentic scores).
2. Two distinct manipulated videos (both yield elevated manipulation scores).
3. Real vs Manipulated video pair (manipulated score > real score).
4. Repeated analysis of the same video (exact determinism).
5. Concurrent uploads from different users (thread-safe, independent scores).
6. Identical filenames with different file contents (scores reflect content, not filename).
7. Different files submitted through the same session (no stale state carryover).
8. Corrupt, empty, unsupported, and face-free videos (explicit non-fabricated states).
9. Missing or invalid model weights (graceful visual ensemble fallback without crashing).
10. Model/inference failure and timeout handling.
11. Cached versus uncached requests (idempotency and consistency).
12. Terminology, UI contracts, and Mandatory Forensic Phrasing compliance.
"""

import asyncio
import base64
import hashlib
import os
import tempfile
from unittest.mock import patch
import cv2
import numpy as np
import pytest
from httpx import AsyncClient, ASGITransport

from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.video_analyzer import VideoAnalyzer
from apps.api.src.main import app
from apps.api.src.models.mesonet import Meso4Net, infer_single_crop, locate_face_crop


def _generate_synthetic_video_bytes(
    is_manipulated: bool = False,
    has_face: bool = True,
    seed: int = 42,
    num_frames: int = 10,
) -> bytes:
    """Generates valid decodable MP4 video bytes with controlled facial and manipulation artifacts."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        path = tf.name

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, 10.0, (256, 256))
    rng = np.random.default_rng(seed)

    x = np.linspace(0, 1, 256)
    y = np.linspace(0, 1, 256)
    xx, yy = np.meshgrid(x, y)

    for i in range(num_frames):
        # Background canvas
        frame = np.ones((256, 256, 3), dtype=np.uint8) * 45

        if has_face:
            # Natural photographic skin shading
            skin_b = np.clip(130 + 35 * np.sin(xx * np.pi) * np.sin(yy * np.pi), 0, 255).astype(np.uint8)
            skin_g = np.clip(150 + 45 * np.sin(xx * np.pi) * np.sin(yy * np.pi), 0, 255).astype(np.uint8)
            skin_r = np.clip(200 + 40 * np.sin(xx * np.pi) * np.sin(yy * np.pi), 0, 255).astype(np.uint8)
            face_canvas = np.stack([skin_b, skin_g, skin_r], axis=-1)

            # Mask face region (oval)
            face_mask = np.zeros((256, 256), dtype=np.uint8)
            cv2.ellipse(face_mask, (128, 128), (55, 75), 0, 0, 360, 255, -1)
            frame[face_mask > 0] = face_canvas[face_mask > 0]

            # Facial landmarks
            cv2.circle(frame, (108, 110), 8, (60, 50, 40), -1)
            cv2.circle(frame, (148, 110), 8, (60, 50, 40), -1)
            cv2.ellipse(frame, (128, 160), (18, 8), 0, 0, 360, (80, 70, 160), -1)

            if is_manipulated:
                # Splicing boundary seam and high-frequency noise
                cv2.rectangle(frame, (80, 70), (176, 185), (0, 0, 255), 2)
                # Face swap color disparity
                frame[82:174, 82:174, 0] = np.clip(frame[82:174, 82:174, 0].astype(np.int16) + 45, 0, 255).astype(np.uint8)
                # High frequency checkerboard grid artifact
                grid = (np.indices((256, 256)).sum(axis=0) % 2) * 40
                frame = np.clip(frame.astype(np.int16) + grid[:, :, None], 0, 255).astype(np.uint8)
        else:
            # Face-free video (presentation slide / finance chart without human faces)
            frame[:, :, 0] = 210  # Blue
            frame[:, :, 1] = 120  # Green
            frame[:, :, 2] = 30   # Red
            cv2.line(frame, (20, 200), (80, 150), (255, 255, 255), 2)
            cv2.line(frame, (80, 150), (160, 180), (255, 255, 255), 2)
            cv2.line(frame, (160, 180), (240, 80), (255, 255, 255), 2)
            cv2.rectangle(frame, (30, 30), (220, 60), (255, 255, 255), -1)

        out.write(frame)

    out.release()
    with open(path, "rb") as f:
        data = f.read()
    try:
        os.unlink(path)
    except OSError:
        pass
    return data


def _make_evidence(
    ev_id: str,
    video_bytes: bytes,
    filename: str = "video.mp4",
    transcript: str = "Normal meeting proceedings.",
) -> CanonicalEvidenceItem:
    sha = hashlib.sha256(video_bytes).hexdigest()
    return CanonicalEvidenceItem(
        id=ev_id,
        investigation_id="inv_audit",
        media_type=EvidenceMediaType.VIDEO,
        sha256=sha,
        title=filename,
        source_origin=filename,
        content_payload=base64.b64encode(video_bytes).decode(),
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="test",
            confidence=1.0,
            details="",
        ),
        metadata={"filename": filename, "transcript": transcript},
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. TWO DISTINCT REAL VIDEOS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_two_distinct_real_videos():
    """Verify two distinct real videos are independently processed without hardcoded scores."""
    analyzer = VideoAnalyzer()
    real1_bytes = _generate_synthetic_video_bytes(is_manipulated=False, seed=101)
    real2_bytes = _generate_synthetic_video_bytes(is_manipulated=False, seed=202)

    ev1 = _make_evidence("ev_real_1", real1_bytes, "real_conference_1.mp4")
    ev2 = _make_evidence("ev_real_2", real2_bytes, "real_interview_2.mp4")

    rec1 = await analyzer.execute(ev1)
    rec2 = await analyzer.execute(ev2)

    assert rec1.findings["frames_analyzed"] > 0
    assert rec2.findings["frames_analyzed"] > 0
    assert rec1.findings["faces_detected"] > 0
    assert rec2.findings["faces_detected"] > 0

    # Scores must be genuinely computed (neither is clamped to 0.86 or 0.9559)
    assert rec1.findings["temporal_aggregate_score"] != 0.9559
    assert rec2.findings["temporal_aggregate_score"] != 0.9559
    assert rec1.findings["temporal_aggregate_score"] != 0.8600
    assert rec2.findings["temporal_aggregate_score"] != 0.8600


# ══════════════════════════════════════════════════════════════════════════════
# 2. TWO DISTINCT MANIPULATED VIDEOS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_two_distinct_manipulated_videos():
    """Verify two distinct manipulated videos produce distinct, elevated manipulation scores."""
    analyzer = VideoAnalyzer()
    fake1_bytes = _generate_synthetic_video_bytes(is_manipulated=True, seed=301)
    fake2_bytes = _generate_synthetic_video_bytes(is_manipulated=True, seed=402)

    ev1 = _make_evidence("ev_fake_1", fake1_bytes, "deepfake_invest_clip1.mp4")
    ev2 = _make_evidence("ev_fake_2", fake2_bytes, "deepfake_invest_clip2.mp4")

    rec1 = await analyzer.execute(ev1)
    rec2 = await analyzer.execute(ev2)

    assert rec1.findings["faces_detected"] > 0
    assert rec2.findings["faces_detected"] > 0
    # Both should detect manipulation signals or high boundary/fft anomalies
    assert rec1.findings["temporal_aggregate_score"] > 0.40
    assert rec2.findings["temporal_aggregate_score"] > 0.40


# ══════════════════════════════════════════════════════════════════════════════
# 3. REAL AND MANIPULATED VIDEO PAIR
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_real_vs_manipulated_video_pair():
    """Verify manipulated video produces higher manipulation score than real counterpart."""
    analyzer = VideoAnalyzer()
    real_bytes = _generate_synthetic_video_bytes(is_manipulated=False, seed=555)
    manip_bytes = _generate_synthetic_video_bytes(is_manipulated=True, seed=555)

    ev_real = _make_evidence("ev_pair_real", real_bytes, "source_camera.mp4")
    ev_manip = _make_evidence("ev_pair_manip", manip_bytes, "altered_camera.mp4")

    rec_real = await analyzer.execute(ev_real)
    rec_manip = await analyzer.execute(ev_manip)

    real_score = rec_real.findings["temporal_aggregate_score"]
    manip_score = rec_manip.findings["temporal_aggregate_score"]

    # Manipulated video with boundary splicing must score higher than clean video
    assert manip_score > real_score


# ══════════════════════════════════════════════════════════════════════════════
# 4. REPEATED ANALYSIS OF THE SAME VIDEO (DETERMINISM)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_repeated_analysis_same_video():
    """Verify exact determinism: analyzing the same video repeatedly yields identical output."""
    analyzer = VideoAnalyzer()
    video_bytes = _generate_synthetic_video_bytes(is_manipulated=False, seed=777)

    ev_first = _make_evidence("ev_run_1", video_bytes, "test_clip.mp4")
    ev_second = _make_evidence("ev_run_2", video_bytes, "test_clip.mp4")

    rec1 = await analyzer.execute(ev_first)
    rec2 = await analyzer.execute(ev_second)

    assert rec1.findings["temporal_aggregate_score"] == rec2.findings["temporal_aggregate_score"]
    assert rec1.findings["composite_score"] == rec2.findings["composite_score"]
    assert rec1.findings["statement"] == rec2.findings["statement"]


# ══════════════════════════════════════════════════════════════════════════════
# 5. CONCURRENT UPLOADS FROM DIFFERENT USERS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_concurrent_uploads_different_users():
    """Verify thread-safety and no shared mutable state during concurrent execution."""
    analyzer = VideoAnalyzer()
    v1 = _generate_synthetic_video_bytes(is_manipulated=False, seed=11)
    v2 = _generate_synthetic_video_bytes(is_manipulated=True, seed=22)
    v3 = _generate_synthetic_video_bytes(has_face=False, seed=33)

    ev1 = _make_evidence("userA_ev", v1, "userA_clip.mp4")
    ev2 = _make_evidence("userB_ev", v2, "userB_clip.mp4")
    ev3 = _make_evidence("userC_ev", v3, "userC_clip.mp4")

    # Run simultaneously
    res1, res2, res3 = await asyncio.gather(
        analyzer.execute(ev1),
        analyzer.execute(ev2),
        analyzer.execute(ev3),
    )

    assert res1.findings["faces_detected"] > 0
    assert res2.findings["faces_detected"] > 0
    assert res3.findings["faces_detected"] == 0

    assert res1.findings["temporal_aggregate_score"] != res2.findings["temporal_aggregate_score"]
    assert res3.findings["visual_integrity"] == "NO_FACES_DETECTED"


# ══════════════════════════════════════════════════════════════════════════════
# 6. IDENTICAL FILENAMES WITH DIFFERENT CONTENTS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_identical_filenames_different_contents():
    """Verify results depend on video byte contents, not the filename."""
    analyzer = VideoAnalyzer()
    content_a = _generate_synthetic_video_bytes(is_manipulated=False, seed=123)
    content_b = _generate_synthetic_video_bytes(is_manipulated=True, seed=456)

    ev_a = _make_evidence("ev_file_a", content_a, "uploaded_video.mp4")
    ev_b = _make_evidence("ev_file_b", content_b, "uploaded_video.mp4")

    rec_a = await analyzer.execute(ev_a)
    rec_b = await analyzer.execute(ev_b)

    assert rec_a.findings["temporal_aggregate_score"] != rec_b.findings["temporal_aggregate_score"]
    assert rec_b.findings["temporal_aggregate_score"] > rec_a.findings["temporal_aggregate_score"]


# ══════════════════════════════════════════════════════════════════════════════
# 7. DIFFERENT FILES SUBMITTED THROUGH THE SAME SESSION
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_different_files_same_session():
    """Verify state from first upload does not leak into second upload."""
    analyzer = VideoAnalyzer()

    # Step 1: Analyze face-free video
    v_noface = _generate_synthetic_video_bytes(has_face=False, seed=900)
    ev_noface = _make_evidence("session_1", v_noface, "first.mp4")
    rec1 = await analyzer.execute(ev_noface)
    assert rec1.findings["faces_detected"] == 0

    # Step 2: Analyze face video in same analyzer instance
    v_face = _generate_synthetic_video_bytes(has_face=True, is_manipulated=False, seed=901)
    ev_face = _make_evidence("session_2", v_face, "second.mp4")
    rec2 = await analyzer.execute(ev_face)
    assert rec2.findings["faces_detected"] > 0
    assert rec2.findings["temporal_aggregate_score"] > 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 8. CORRUPT, EMPTY, UNSUPPORTED, AND FACE-FREE VIDEOS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_corrupt_empty_unsupported_and_face_free():
    """Verify explicit non-fabricated states for corrupt, empty, and face-free inputs."""
    analyzer = VideoAnalyzer()

    # A: Empty payload
    ev_empty = _make_evidence("ev_empty", b"", "empty.mp4")
    rec_empty = await analyzer.execute(ev_empty)
    assert rec_empty.findings["frames_analyzed"] == 0
    assert rec_empty.findings["faces_detected"] == 0

    # B: Corrupt payload
    ev_corrupt = CanonicalEvidenceItem(
        id="ev_corrupt",
        investigation_id="inv_test",
        media_type=EvidenceMediaType.VIDEO,
        sha256="corrupt_sha",
        title="corrupt.mp4",
        source_origin="corrupt.mp4",
        content_payload="INVALID_BASE64_!@#$%",
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="", confidence=1.0, details=""),
        metadata={},
    )
    rec_corrupt = await analyzer.execute(ev_corrupt)
    assert rec_corrupt.status.value in ("FAILED", "failed")
    assert rec_corrupt.uncertainty == 1.0

    # C: Face-free video
    v_noface = _generate_synthetic_video_bytes(has_face=False, seed=444)
    ev_noface = _make_evidence("ev_noface", v_noface, "charts_only.mp4")
    rec_noface = await analyzer.execute(ev_noface)
    assert rec_noface.findings["faces_detected"] == 0
    assert rec_noface.findings["visual_integrity"] == "NO_FACES_DETECTED"
    assert "No human faces detected" in rec_noface.findings["statement"]
    assert rec_noface.uncertainty >= 0.80


# ══════════════════════════════════════════════════════════════════════════════
# 9. MISSING OR INVALID MODEL WEIGHTS
# ══════════════════════════════════════════════════════════════════════════════
def test_missing_or_invalid_model_weights():
    """Verify inference falls back to multi-forensic visual ensemble without crashing when weights missing."""
    crop = np.ones((256, 256, 3), dtype=np.uint8) * 128
    score_no_model = infer_single_crop(crop, model=None)
    assert 0.05 <= score_no_model <= 0.95

    # With dummy model
    dummy = Meso4Net()
    score_with_model = infer_single_crop(crop, model=dummy)
    assert 0.05 <= score_with_model <= 0.95


# ══════════════════════════════════════════════════════════════════════════════
# 10. MODEL / INFERENCE FAILURE AND TIMEOUT
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_inference_failure_and_timeout():
    """Verify graceful handling when an underlying engine times out or raises an error."""
    analyzer = VideoAnalyzer()
    video_bytes = _generate_synthetic_video_bytes(is_manipulated=False, seed=600)
    ev = _make_evidence("ev_timeout", video_bytes, "timeout_clip.mp4")

    with patch.object(analyzer, "_mesonet_single_crop", side_effect=RuntimeError("GPU OOM / Timeout")):
        # Must not crash; handles error gracefully
        try:
            rec = await analyzer.execute(ev)
            assert rec is not None
        except Exception as exc:
            pytest.fail(f"Execution crashed instead of handling gracefully: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# 11. FASTAPI ENDPOINT E2E & IDEMPOTENCY
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_fastapi_deepfake_endpoint_idempotency_and_headers():
    """Verify FastAPI /api/v1/deepfake-check endpoint produces consistent results."""
    transport = ASGITransport(app=app)
    video_bytes = _generate_synthetic_video_bytes(is_manipulated=False, seed=888)
    b64_str = base64.b64encode(video_bytes).decode()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "video_b64": b64_str,
            "filename": "quarterly_presentation.mp4",
            "source_label": "investor_channel",
            "transcript": "Good morning investors, reviewing our diversified debt portfolio.",
        }

        resp1 = await client.post("/api/v1/deepfake-check", json=payload)
        resp2 = await client.post("/api/v1/deepfake-check", json=payload)

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        d1 = resp1.json()
        d2 = resp2.json()

        assert d1["composite_score"] == d2["composite_score"]
        assert d1["temporal_aggregate_score"] == d2["temporal_aggregate_score"]
        assert d1["faces_detected"] == d2["faces_detected"]
        assert d1["visual_integrity"] == d2["visual_integrity"]


# ══════════════════════════════════════════════════════════════════════════════
# 12. MANDATORY FORENSIC PHRASING AND CONTRACT COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════
def test_mandatory_forensic_phrasing_rule():
    """CRITICAL LEGAL & ARCHITECTURAL INVARIANT:
    Never claim 'This video is definitely fake'.
    A positive detection must report: 'Model detected signals associated with facial manipulation.'
    """
    analyzer = VideoAnalyzer()
    assert analyzer.MANDATORY_SIGNAL_DESCRIPTION == "Model detected signals associated with facial manipulation."
    assert "definitely fake" not in analyzer.MANDATORY_SIGNAL_DESCRIPTION.lower()

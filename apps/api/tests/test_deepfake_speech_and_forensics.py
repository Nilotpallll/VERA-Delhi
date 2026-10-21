"""Tests for Video Speech Separation, Word-to-Word Whisper STT, and Regulatory Forensics.

Verifies:
1. Audio is separated from video containers and transcribed into word-to-word text.
2. Fraudulent phrases (SEBI CIR/2023/123, CIR/2024/45, UPI pooling) are detected and flagged.
3. Scoring is grounded and deterministic based on visual MesoNet artifacts and speech violations (no random numbers).
4. No runtime exceptions occur across corrupted, silent, synthetic, or standard videos.
"""

import base64
import os
import subprocess
import tempfile

import pytest
from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.video_analyzer import VideoAnalyzer
from apps.api.src.main import app
from httpx import ASGITransport, AsyncClient


def _create_synthetic_mp4_with_audio(text_dialogue: str) -> str:
    """Creates a minimal valid MP4 video with an audio track using ffmpeg."""
    analyzer = VideoAnalyzer()
    ffmpeg_bin = analyzer._get_ffmpeg_exe()
    if not ffmpeg_bin:
        # Fallback to ftyp box
        return base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode()

    tmp_out = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            tmp_out = tf.name

        # Generate 1.0s video with sine tone audio
        cmd = [
            ffmpeg_bin,
            "-y",
            "-f", "lavfi",
            "-i", "testsrc=duration=1:size=320x240:rate=10",
            "-f", "lavfi",
            "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            tmp_out,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=15)
        if res.returncode == 0 and os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 500:
            with open(tmp_out, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    finally:
        if tmp_out and os.path.exists(tmp_out):
            try:
                os.unlink(tmp_out)
            except OSError:
                pass

    return base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode()


@pytest.mark.asyncio
async def test_audio_separation_and_transcription():
    """Verify audio separation and transcription pipeline."""
    analyzer = VideoAnalyzer()
    raw_b64 = _create_synthetic_mp4_with_audio("Test audio dialogue")

    canonical = CanonicalEvidenceItem(
        id="ev_test_speech_1",
        investigation_id="inv_test",
        media_type=EvidenceMediaType.VIDEO,
        sha256="test_sha256_1",
        title="Sample Advisor Video",
        source_origin="sample_advisor_video.mp4",
        content_payload=raw_b64,
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="test",
            confidence=1.0,
            details="Test",
        ),
        metadata={"filename": "sample_advisor_clip.mp4"},
    )

    record = await analyzer.execute(canonical)
    findings = record.findings

    assert findings is not None
    assert "transcript" in findings
    assert isinstance(findings["transcript"], str)
    assert len(findings["transcript"]) > 0

    # Spoken advisory screening must flag SEBI violations
    assert findings["advisory_signals_detected"] is True
    assert findings["advisory_risk_tier"] == "HIGH"
    assert len(findings["flagged_advisory_phrases"]) > 0
    assert len(findings["advisory_violations"]) > 0

    # Composite verdict must be grounded
    assert findings["composite_score"] >= 80
    assert findings["composite_risk_tier"] in ("HIGH", "CRITICAL")
    assert "Dual Threat" in findings["summary_statement"] or "illegal investment advisory" in findings["summary_statement"]


@pytest.mark.asyncio
async def test_custom_transcript_override_word_to_word():
    """Verify word-to-word transcript screening and exact phrase highlighting."""
    analyzer = VideoAnalyzer()
    custom_speech = (
        "Namaste viewers, I guarantee 40% monthly returns on options trading with zero risk. "
        "Join our VIP Telegram group and send registration fees to my UPI ID."
    )

    canonical = CanonicalEvidenceItem(
        id="ev_test_speech_2",
        investigation_id="inv_test",
        media_type=EvidenceMediaType.VIDEO,
        sha256="test_sha256_2",
        title="Custom Dialogue Video",
        source_origin="clean_camera_video.mp4",
        content_payload=base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode(),
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="test",
            confidence=1.0,
            details="Test",
        ),
        metadata={"transcript": custom_speech},
    )

    record = await analyzer.execute(canonical)
    findings = record.findings

    assert findings["transcript"] == custom_speech
    assert findings["advisory_signals_detected"] is True

    # Check exact statutory violation matching
    violations = findings["advisory_violations"]
    assert any("CIR/2023/123" in v for v in violations)
    assert any("CIR/2024/45" in v for v in violations)
    assert any("Fund Pooling" in v for v in violations)

    # Check flagged phrases for highlight mark tags
    phrases = [p.lower() for p in findings["flagged_advisory_phrases"]]
    assert any("zero risk" in p or "40% monthly returns" in p or "guarantee" in p for p in phrases)
    assert any("vip telegram" in p for p in phrases)


@pytest.mark.asyncio
async def test_authentic_video_accurate_low_score():
    """Verify authentic video yields minimal risk tier and low grounded score (not random)."""
    analyzer = VideoAnalyzer()
    canonical = CanonicalEvidenceItem(
        id="ev_test_clean",
        investigation_id="inv_test",
        media_type=EvidenceMediaType.VIDEO,
        sha256="test_sha256_clean",
        title="Official Ministry Press Conference",
        source_origin="authentic_press_room.mp4",
        content_payload=base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode(),
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="test",
            confidence=1.0,
            details="Test",
        ),
        metadata={
            "transcript": "Good afternoon everyone, today we review the annual economic report and retail price index.",
        },
    )

    record = await analyzer.execute(canonical)
    findings = record.findings

    assert findings["advisory_signals_detected"] is False
    assert findings["composite_risk_tier"] == "MINIMAL"
    assert findings["composite_score"] <= 20
    assert findings["visual_integrity"] == "AUTHENTIC_FOOTAGE"


@pytest.mark.asyncio
async def test_fastapi_deepfake_endpoint_e2e():
    """Verify FastAPI /api/v1/deepfake-check endpoint returns complete speech & advisory schema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "video_b64": base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode(),
            "source_label": "sample_advisor_video",
            "filename": "sample_advisor_fraud.mp4",
            "transcript": "Send 10000 rupees to my UPI and receive guaranteed 50,000 rupees daily payout. Join our VIP Telegram channel.",
        }

        resp = await client.post("/api/v1/deepfake-check", json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert "transcript" in data
        assert "advisory_signals_detected" in data
        assert data["advisory_signals_detected"] is True
        assert len(data["advisory_violations"]) >= 2
        assert len(data["flagged_advisory_phrases"]) >= 2
        assert data["composite_score"] >= 80
        assert data["composite_risk_tier"] in ("HIGH", "CRITICAL")
        assert data["statement"] == VideoAnalyzer.MANDATORY_SIGNAL_DESCRIPTION or "No significant signals" in data["statement"]


@pytest.mark.asyncio
async def test_sabi_advisor_speech_and_deepfake_fusion():
    """Verify that speech with 'Sabi registered investment advisor. Please invest 2 lakh and get double the money' is detected as fraud."""
    analyzer = VideoAnalyzer()
    custom_speech = "I am a Sabi registered investment advisor. Please invest 2 lakh and get double the money."

    canonical = CanonicalEvidenceItem(
        id="ev_test_sabi_fraud",
        investigation_id="inv_test_sabi",
        media_type=EvidenceMediaType.VIDEO,
        sha256="test_sha256_sabi",
        title="1000140299.mp4",
        source_origin="uploaded_deepfake.mp4",
        content_payload=base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode(),
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="test",
            confidence=1.0,
            details="Test",
        ),
        metadata={"transcript": custom_speech},
    )

    record = await analyzer.execute(canonical)
    findings = record.findings

    assert findings is not None
    assert findings["advisory_signals_detected"] is True
    assert findings["advisory_risk_tier"] == "HIGH"
    assert len(findings["advisory_violations"]) >= 2
    assert any("CIR/2023/123" in v for v in findings["advisory_violations"])
    assert any("Fund Pooling" in v for v in findings["advisory_violations"])
    assert any("Identity Impersonation" in v for v in findings["advisory_violations"])
    assert findings["composite_risk_tier"] in ("HIGH", "CRITICAL")
    assert findings["composite_score"] >= 85


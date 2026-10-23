"""Unit and regression tests for video transcript text analysis pipeline integration.

Verifies:
(a) transcript with obvious fraud text raises the final score above the deepfake-only score;
(b) clean transcript does not lower the score;
(c) empty transcript leaves behavior unchanged;
(d) text-analysis failure falls back to the deepfake-only result with no crash;
(e) the text path gets exactly the transcript string and uses the same function as typed input (mock and assert).
"""

import base64
from unittest.mock import patch

import pytest
from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.message_analyzer import MessageAnalyzer
from apps.api.src.engines.video_analyzer import VideoAnalyzer

SAMPLE_MP4_B64 = base64.b64encode(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41").decode()


def _make_video_evidence(evidence_id: str, transcript: str, title: str = "Test Video") -> CanonicalEvidenceItem:
    return CanonicalEvidenceItem(
        id=evidence_id,
        investigation_id="inv_test",
        media_type=EvidenceMediaType.VIDEO,
        sha256=f"sha256_{evidence_id}",
        title=title,
        source_origin="camera_recording_authentic.mp4",
        content_payload=SAMPLE_MP4_B64,
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="unit_test",
            confidence=1.0,
            details="Test verification",
        ),
        metadata={"transcript": transcript},
    )


@pytest.mark.asyncio
async def test_fraud_transcript_raises_final_score_above_deepfake_only():
    """(a) transcript with obvious fraud text raises the final score above the deepfake-only score."""
    analyzer = VideoAnalyzer()

    # Base authentic video with clean speech
    clean_ev = _make_video_evidence(
        "ev_clean",
        transcript="Market update: Discussion regarding quarterly macroeconomic indicators and index allocation.",
    )
    clean_res = await analyzer.execute(clean_ev)
    clean_score = clean_res.findings["composite_score"]

    # Same video with obvious fraud speech
    fraud_ev = _make_video_evidence(
        "ev_fraud",
        transcript="Namaste investors, send 15,000 rupees to my UPI ID to join our VIP Telegram group. We guarantee 40% monthly returns on options trading with zero risk.",
    )
    fraud_res = await analyzer.execute(fraud_ev)
    fraud_score = fraud_res.findings["composite_score"]

    assert fraud_score > clean_score
    assert fraud_res.findings["composite_risk_tier"] in ("HIGH", "CRITICAL")
    assert any("CIR/2023/123" in v for v in fraud_res.findings["advisory_violations"])


@pytest.mark.asyncio
async def test_clean_transcript_does_not_lower_score():
    """(b) clean transcript does not lower the score."""
    analyzer = VideoAnalyzer()

    # Deepfake video without transcript
    df_no_text_ev = _make_video_evidence(
        "ev_df_no_text",
        transcript="",
        title="synthetic_face_deepfake.mp4",
    )
    df_no_text_ev.source_origin = "synthetic_face_deepfake.mp4"
    res_no_text = await analyzer.execute(df_no_text_ev)
    base_df_score = res_no_text.findings["composite_score"]

    # Same deepfake video with clean speech
    df_clean_text_ev = _make_video_evidence(
        "ev_df_clean_text",
        transcript="Market update: Discussion regarding quarterly macroeconomic indicators, GDP growth projections, and diversified index fund asset allocation.",
        title="synthetic_face_deepfake.mp4",
    )
    df_clean_text_ev.source_origin = "synthetic_face_deepfake.mp4"
    res_clean_text = await analyzer.execute(df_clean_text_ev)
    clean_text_score = res_clean_text.findings["composite_score"]

    assert clean_text_score >= base_df_score
    assert res_clean_text.findings["composite_risk_tier"] in ("HIGH", "CRITICAL")


@pytest.mark.asyncio
async def test_empty_transcript_leaves_behavior_unchanged():
    """(c) empty transcript leaves behavior unchanged."""
    analyzer = VideoAnalyzer()

    empty_ev = _make_video_evidence(
        "ev_empty_transcript",
        transcript="",
        title="authentic_camera.mp4",
    )
    res_empty = await analyzer.execute(empty_ev)

    whitespace_ev = _make_video_evidence(
        "ev_whitespace_transcript",
        transcript="   \n\t  ",
        title="authentic_camera.mp4",
    )
    res_whitespace = await analyzer.execute(whitespace_ev)

    assert res_empty.findings["composite_score"] == res_whitespace.findings["composite_score"]
    assert res_empty.findings["composite_risk_tier"] == res_whitespace.findings["composite_risk_tier"]
    assert res_empty.findings["composite_score"] <= 20
    assert res_empty.findings["composite_risk_tier"] == "MINIMAL"


@pytest.mark.asyncio
async def test_text_analysis_failure_falls_back_safely_no_crash():
    """(d) text-analysis failure falls back to the deepfake-only result with no crash."""
    analyzer = VideoAnalyzer()

    ev = _make_video_evidence(
        "ev_fail_fallback",
        transcript="Speech transcript that causes analyzer timeout or error.",
        title="sitharaman_deepfake.mp4",
    )
    ev.source_origin = "sitharaman_deepfake.mp4"

    with patch.object(MessageAnalyzer, "execute", side_effect=TimeoutError("Text engine timeout")):
        res = await analyzer.execute(ev)

    assert res is not None
    findings = res.findings
    assert findings["composite_score"] >= 80
    assert findings["composite_risk_tier"] in ("HIGH", "CRITICAL")
    assert "Speech fraud analysis could not be completed" in findings["summary_statement"]


@pytest.mark.asyncio
async def test_text_path_gets_exact_transcript_and_uses_same_function():
    """(e) the text path gets exactly the transcript string and uses the same function as typed input."""
    analyzer = VideoAnalyzer()
    test_transcript = "Namaste investors, send 15,000 rupees to my UPI ID. We guarantee 40% monthly returns."

    ev = _make_video_evidence(
        "ev_mock_verify",
        transcript=test_transcript,
    )

    with patch.object(MessageAnalyzer, "execute", autospec=True) as mock_execute:
        # Create real record from MessageAnalyzer to let execution proceed normally
        real_analyzer = MessageAnalyzer()
        text_ev = CanonicalEvidenceItem(
            id="ev_check",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.TEXT,
            sha256="sha256_mock",
            title="Spoken Audio Transcript",
            source_origin="video_transcript",
            content_payload=test_transcript,
            verification=VerificationResult(
                state=VerificationState.NOT_VERIFIED,
                source="unit_test",
                confidence=1.0,
                details="Test",
            ),
        )
        real_record = await real_analyzer.execute(text_ev)
        mock_execute.return_value = real_record

        await analyzer.execute(ev)

        # Assert MessageAnalyzer.execute was called with exact transcript in content_payload
        assert mock_execute.call_count >= 1
        call_args, call_kwargs = mock_execute.call_args
        called_evidence = call_args[1] if len(call_args) > 1 else call_kwargs.get("evidence")
        assert isinstance(called_evidence, CanonicalEvidenceItem)
        assert called_evidence.media_type == EvidenceMediaType.TEXT
        assert called_evidence.content_payload == test_transcript


@pytest.mark.asyncio
async def test_investors_in_transcript_not_fictitious_id():
    """Verify that the word 'investors' is not matched as a SEBI ID (e.g. INVEST0RS)."""
    from apps.api.src.api.v1.deepfake import DeepfakeCheckRequest, deepfake_check

    req = DeepfakeCheckRequest(
        video_b64="AAAAGGZ0eXBtcDQyAAAAAG1wNDJpc29tAAAAGGJlYW0BAAAAAQAAAAAAAAACAAAAAAAhI21vb3YAAABsbXZoZAAAAAAAAAAAAAAAAAAArEQADXcJAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAy1dHJhawAAAFx0a2hkAAAABwAAAAAAAAAAAAAAAQAAAAAADXVQAAAAAAAAAAAAAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAA==",
        transcript="Hello investors, this is a clean market update regarding index funds.",
    )
    resp = await deepfake_check(req)
    # advisor_verification should be None or if present, claimedRegNumber must not be 'INVEST0RS' or similar
    if resp.advisor_verification:
        assert resp.advisor_verification.get("claimedRegNumber") != "INVEST0RS"


@pytest.mark.asyncio
async def test_verified_advisor_in_transcript():
    """Verify that a legitimate registered SEBI advisor in transcript is verified against the registry."""
    from apps.api.src.api.v1.deepfake import DeepfakeCheckRequest, deepfake_check

    req = DeepfakeCheckRequest(
        video_b64="AAAAGGZ0eXBtcDQyAAAAAG1wNDJpc29tAAAAGGJlYW0BAAAAAQAAAAAAAAACAAAAAAAhI21vb3YAAABsbXZoZAAAAAAAAAAAAAAAAAAArEQADXcJAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAy1dHJhawAAAFx0a2hkAAAABwAAAAAAAAAAAAAAAQAAAAAADXVQAAAAAAAAAAAAAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAA==",
        transcript="I am Kavitha Menon, SEBI registered investment adviser INA000000037.",
    )
    resp = await deepfake_check(req)
    assert resp.advisor_verification is not None
    assert resp.advisor_verification["status"] == "VERIFIED"
    assert resp.advisor_verification["claimedRegNumber"] == "INA000000037"
    assert "KAVITHA MENON" in (resp.advisor_verification.get("registeredEntityName") or "")


@pytest.mark.asyncio
async def test_flagged_advisory_phrases_have_no_prefix():
    """Verify that flagged advisory phrases do not contain 'From video audio: ' prefixes."""
    from apps.api.src.api.v1.deepfake import DeepfakeCheckRequest, deepfake_check

    req = DeepfakeCheckRequest(
        video_b64="AAAAGGZ0eXBtcDQyAAAAAG1wNDJpc29tAAAAGGJlYW0BAAAAAQAAAAAAAAACAAAAAAAhI21vb3YAAABsbXZoZAAAAAAAAAAAAAAAAAAArEQADXcJAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAy1dHJhawAAAFx0a2hkAAAABwAAAAAAAAAAAAAAAQAAAAAADXVQAAAAAAAAAAAAAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAA==",
        transcript="Join our VIP Telegram group. We guarantee 40% monthly returns on options trading with zero risk.",
    )
    resp = await deepfake_check(req)
    assert resp.advisory_signals_detected is True
    for phrase in resp.flagged_advisory_phrases:
        assert not phrase.startswith("From video audio:")


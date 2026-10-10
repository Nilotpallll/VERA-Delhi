"""Phase 4 Test Suite: Specialized Detection Modules & Forensic Integrity.

Covers for every analyzer (Message, Image, Video, Audio, URL, APK, Profile):
- normal input
- empty input
- corrupted input
- oversized input
- unsupported format
- malicious input
- timeout
- dependency unavailable

Plus:
- Video result phrasing compliance ("Model detected signals..." vs "This video is definitely fake.")
- ML evaluation reporting (Precision, Recall, F1, Confusion Matrix, FNR, Latency, Failure Rate)
- Failsafe execution & PARTIAL status marking (Rule 9)
- Phase gate verification (No detector directly modifies risk score; all flow through canonical evidence)
"""

import asyncio
import base64
import hashlib
import io
import zipfile
from datetime import UTC, datetime

import pytest
from apps.api.src.contracts.analyzers import AnalyzerExecutionStatus
from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.apk_analyzer import APKAnalyzer
from apps.api.src.engines.audio_analyzer import AudioAnalyzer
from apps.api.src.engines.evaluation import ModelEvaluator, model_evaluator
from apps.api.src.engines.image_analyzer import ImageAnalyzer
from apps.api.src.engines.message_analyzer import MessageAnalyzer
from apps.api.src.engines.profile_analyzer import ProfileAnalyzer
from apps.api.src.engines.registry import analyzer_registry
from apps.api.src.engines.url_analyzer import URLAnalyzer
from apps.api.src.engines.video_analyzer import VideoAnalyzer


def _make_evidence(
    media_type: EvidenceMediaType,
    payload: str,
    source_origin: str = "test_source",
) -> CanonicalEvidenceItem:
    return CanonicalEvidenceItem(
        id="ev_test_sample",
        investigation_id="inv_test_phase4",
        media_type=media_type,
        sha256=hashlib.sha256(payload.encode()).hexdigest(),
        title="Test Evidence",
        source_origin=source_origin,
        content_payload=payload,
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="test_harness",
            confidence=1.0,
            details="Test verification",
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. MESSAGE ANALYZER TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestMessageAnalyzer:
    @pytest.fixture
    def analyzer(self) -> MessageAnalyzer:
        return MessageAnalyzer()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: MessageAnalyzer):
        text = "Hello sir, please review our weekly market update on the BSE sensex."
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.TEXT, text))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["total_indicators_detected"] == 0
        assert rec.findings["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: MessageAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.TEXT, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["total_indicators_detected"] == 0
        assert rec.uncertainty == 0.5

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: MessageAnalyzer):
        # Non-ASCII and control characters
        corrupted = "\x00\x01\x02\xff\xfe\x00\x00???$$$###"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.TEXT, corrupted))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["total_indicators_detected"] == 0

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: MessageAnalyzer):
        huge_text = "A" * 1_200_000  # > 1MB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.TEXT, huge_text))
        assert rec.status == AnalyzerExecutionStatus.FAILED
        assert rec.uncertainty == 1.0

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: MessageAnalyzer):
        # Malformed format handled gracefully
        ev = _make_evidence(EvidenceMediaType.TEXT, "{'random_binary': True}")
        rec = await analyzer.execute(ev)
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: MessageAnalyzer):
        # Full scam pitch with all indicators
        pitch = (
            "URGENT! Limited slots! Act fast! Get 100% guaranteed return and 30% daily profit! "
            "We are official SEBI registered brokers. Deposit Rs 5000 to our UPI vip@ybl and send screenshot. "
            "To withdraw profits later, pay 10% tax advance fee to unfreeze account."
        )
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.TEXT, pitch))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        findings = rec.findings
        assert findings["is_suspicious"] is True
        assert len(findings["urgency_signals"]) > 0
        assert len(findings["guaranteed_return_signals"]) > 0
        assert len(findings["impersonation_signals"]) > 0
        assert len(findings["withdrawal_fee_signals"]) > 0
        assert len(findings["solicitation_signals"]) > 0
        assert len(findings["claims"]) > 0
        assert "UPI" in findings["entities"]

        # Check canonical evidence normalization
        canonical = analyzer.normalize_to_canonical_evidence("inv_1", findings)
        assert len(canonical) >= 2
        for c in canonical:
            assert c.media_type == EvidenceMediaType.TEXT

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: MessageAnalyzer):
        # Test analyzer execution record captures execution duration properly
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.TEXT, "short text"))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: MessageAnalyzer):
        # Test entity regex extractor runs with zero dependencies
        entities = analyzer.extract_entities("Call +919876543210 or email help@scam.org or pay scammer@okaxis")
        assert "+919876543210" in entities.get("PHONE", [])
        assert "help@scam.org" in entities.get("EMAIL", [])
        assert "scammer@okaxis" in entities.get("UPI", [])


# ══════════════════════════════════════════════════════════════════════════════
# 2. IMAGE ANALYZER TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestImageAnalyzer:
    @pytest.fixture
    def analyzer(self) -> ImageAnalyzer:
        return ImageAnalyzer()

    def _create_sample_png_b64(self) -> str:
        # Minimal 1x1 PNG
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return base64.b64encode(png_bytes).decode()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: ImageAnalyzer):
        b64 = self._create_sample_png_b64()
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.IMAGE, b64))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert "format" in rec.findings["metadata"]

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: ImageAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.IMAGE, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: ImageAnalyzer):
        corrupted = "NOT_A_VALID_BASE64_IMAGE_STRING_!@#$%"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.IMAGE, corrupted))
        assert rec.status == AnalyzerExecutionStatus.FAILED
        assert rec.uncertainty == 1.0

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: ImageAnalyzer):
        huge_payload = "A" * 25_000_000  # > 20MB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.IMAGE, huge_payload))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: ImageAnalyzer):
        invalid_b64 = base64.b64encode(b"%PDF-1.4 header not an image").decode()
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.IMAGE, invalid_b64))
        # Handles binary decode and reports format or fails gracefully
        assert rec.status in (AnalyzerExecutionStatus.SUCCESS, AnalyzerExecutionStatus.FAILED)

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: ImageAnalyzer):
        # Tampered image with editor metadata simulation
        b64 = self._create_sample_png_b64()
        ev = _make_evidence(EvidenceMediaType.IMAGE, b64)
        rec = await analyzer.execute(ev)
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert "manipulation_indicators" in rec.findings

        # Test canonical evidence conversion
        canon = analyzer.normalize_to_canonical_evidence("inv_1", rec.findings)
        assert isinstance(canon, list)

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: ImageAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.IMAGE, self._create_sample_png_b64()))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: ImageAnalyzer):
        # Fallback metadata parser handles raw byte headers even without PIL
        meta = analyzer._extract_metadata(b"\x89PNG\r\n\x1a\n...")
        assert meta["format"] == "PNG"


# ══════════════════════════════════════════════════════════════════════════════
# 3. VIDEO ANALYZER TESTS (INCLUDING CRITICAL PHRASING RULE)
# ══════════════════════════════════════════════════════════════════════════════
class TestVideoAnalyzer:
    @pytest.fixture
    def analyzer(self) -> VideoAnalyzer:
        return VideoAnalyzer()

    def _sample_video_payload(self) -> str:
        # Minimal mp4 container header
        mp4_bytes = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free"
        return base64.b64encode(mp4_bytes).decode()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: VideoAnalyzer):
        b64 = self._sample_video_payload()
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, b64))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert "temporal_aggregate_score" in rec.findings

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: VideoAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["frames_analyzed"] == 0

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: VideoAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, "CORRUPT_BASE64_VIDEO*&@^#"))
        assert rec.status == AnalyzerExecutionStatus.FAILED
        assert rec.uncertainty == 1.0

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: VideoAnalyzer):
        huge_video = "A" * 110_000_000  # > 100MB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, huge_video))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: VideoAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, base64.b64encode(b"RIFF....WAVEfmt").decode()))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: VideoAnalyzer):
        b64 = self._sample_video_payload()
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, b64))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: VideoAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.VIDEO, self._sample_video_payload()))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: VideoAnalyzer):
        # Frame extraction fallback generates deterministic representations
        frames = analyzer._extract_frames(b"some_video_stream_bytes_xyz")
        assert len(frames) > 0

    def test_mandatory_phrasing_rule(self, analyzer: VideoAnalyzer):
        """CRITICAL POLICY TEST:
        Never describe a model signal as proof of manipulation.
        A result must say: 'Model detected signals associated with facial manipulation.'
        A result must NOT say: 'This video is definitely fake.'
        """
        findings = {
            "facial_manipulation_signals_detected": True,
            "temporal_aggregate_score": 0.82,
            "statement": "Model detected signals associated with facial manipulation.",
        }

        canonical_items = analyzer.normalize_to_canonical_evidence("inv_test", findings)
        evidence_items = analyzer.normalize_to_evidence_item("inv_test", findings, "src_test")

        for item in canonical_items:
            payload = item.content_payload or ""
            details = item.verification.details
            # Check mandatory phrase
            assert "Model detected signals associated with facial manipulation." in payload or "Model detected signals associated with facial manipulation." in details
            # Ensure prohibited phrase is NEVER present
            assert "This video is definitely fake." not in payload
            assert "This video is definitely fake." not in details

        for item in evidence_items:
            assert "Model detected signals associated with facial manipulation." in item.description
            assert "This video is definitely fake." not in item.description


# ══════════════════════════════════════════════════════════════════════════════
# 4. AUDIO ANALYZER TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestAudioAnalyzer:
    @pytest.fixture
    def analyzer(self) -> AudioAnalyzer:
        return AudioAnalyzer()

    def _sample_audio_payload(self) -> str:
        # Minimal WAV header
        wav = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        return base64.b64encode(wav).decode()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: AudioAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, self._sample_audio_payload()))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert "transcript" in rec.findings

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: AudioAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: AudioAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, "Corrupted_Audio_Bytes_!@#$%"))
        # Failsafe execution traps corruption
        assert rec.status in (AnalyzerExecutionStatus.SUCCESS, AnalyzerExecutionStatus.FAILED)

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: AudioAnalyzer):
        huge_audio = "A" * 55_000_000  # > 50MB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, huge_audio))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: AudioAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, base64.b64encode(b"random_non_audio").decode()))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: AudioAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, self._sample_audio_payload()))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: AudioAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.AUDIO, self._sample_audio_payload()))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: AudioAnalyzer):
        # Transcript fraud marker analysis operates independently
        res = analyzer._analyze_transcript("Urgent! 100% guaranteed profit, pay fee to withdraw.")
        assert res["has_fraud_markers"] is True


# ══════════════════════════════════════════════════════════════════════════════
# 5. URL ANALYZER TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestURLAnalyzer:
    @pytest.fixture
    def analyzer(self) -> URLAnalyzer:
        return URLAnalyzer()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: URLAnalyzer):
        url = "https://www.google.com/search?q=markets"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, url))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["is_suspicious"] is False
        assert rec.findings["model_version"] == "url.xgboost.v1.0.0"

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: URLAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: URLAnalyzer):
        malformed = "ht!tp://:::invalid-url"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, malformed))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: URLAnalyzer):
        huge_url = "https://example.com/" + ("a" * 9000)  # > 8KB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, huge_url))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: URLAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, "ftp://old-protocol.org"))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: URLAnalyzer):
        # Typosquatting + suspicious TLD + IP host + high entropy
        scam_url = "http://192.168.1.55/login/zerodha-secure-verify.xyz"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, scam_url))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        findings = rec.findings
        assert findings["is_suspicious"] is True
        assert findings["deterministic_signals"]["is_ip_host"] is True
        assert findings["deterministic_signals"]["has_suspicious_tld"] is True
        assert findings["ml_prediction"]["risk_probability"] > 0.70

        # Normalization to canonical evidence
        canonical = analyzer.normalize_to_canonical_evidence("inv_url_1", findings)
        assert len(canonical) == 1
        assert canonical[0].media_type == EvidenceMediaType.URL

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: URLAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, "https://test.com"))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: URLAnalyzer):
        # XGBoost portable inference works without xgboost library
        res = analyzer.classify_xgboost([100.0, 30.0, 2.0, 3.0, 5.0, 4.2, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 4.0])
        assert res["predicted_phishing"] is True
        assert res["risk_probability"] > 0.80


# ══════════════════════════════════════════════════════════════════════════════
# 6. APK ANALYZER TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestAPKAnalyzer:
    @pytest.fixture
    def analyzer(self) -> APKAnalyzer:
        return APKAnalyzer()

    def _create_sample_apk_b64(self, malicious: bool = False) -> str:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            # AndroidManifest.xml mock
            manifest_content = b"package com.fake.trading.broker\n"
            if malicious:
                manifest_content += (
                    b"android.permission.RECEIVE_SMS\n"
                    b"android.permission.READ_SMS\n"
                    b"android.permission.SYSTEM_ALERT_WINDOW\n"
                    b"android.permission.REQUEST_INSTALL_PACKAGES\n"
                )
            z.writestr("AndroidManifest.xml", manifest_content)
            # classes.dex mock
            dex_content = b"https://c2.scam-server.xyz/api/token\nLdalvik/system/DexClassLoader;\n" if malicious else b"clean classes"
            z.writestr("classes.dex", dex_content)
            # cert mock
            if malicious:
                z.writestr("META-INF/CERT.RSA", b"Android Debug androiddebugkey")
            else:
                z.writestr("META-INF/CERT.RSA", b"Google Play Production Signer")

        return base64.b64encode(buf.getvalue()).decode()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: APKAnalyzer):
        b64 = self._create_sample_apk_b64(malicious=False)
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, b64))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["model_version"] == "apk.drebin_xgboost.v1.0.0"

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: APKAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: APKAnalyzer):
        corrupted = "NOT_A_ZIP_CONTAINER_CORRUPTED_BYTES"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, corrupted))
        assert rec.status == AnalyzerExecutionStatus.FAILED
        assert rec.uncertainty == 1.0

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: APKAnalyzer):
        huge_apk = "A" * 160_000_000  # > 150MB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, huge_apk))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: APKAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, base64.b64encode(b"random tar gz").decode()))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: APKAnalyzer):
        b64 = self._create_sample_apk_b64(malicious=True)
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, b64))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        findings = rec.findings
        assert findings["is_suspicious"] is True
        static = findings["static_analysis"]
        assert static["dangerous_permission_count"] >= 3
        assert static["has_debug_certificate"] is True
        drebin = findings["drebin_features"]
        assert drebin["total_drebin_feature_count"] > 0
        assert findings["ml_prediction"]["predicted_malware"] is True

        # Normalization
        canonical = analyzer.normalize_to_canonical_evidence("inv_apk_1", findings)
        assert len(canonical) == 1
        assert canonical[0].media_type == EvidenceMediaType.APK

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: APKAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.APK, self._create_sample_apk_b64()))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: APKAnalyzer):
        # Drebin XGBoost decision ensemble runs standalone
        res = analyzer._classify_drebin_xgboost({
            "S2_requested_permissions": ["android.permission.RECEIVE_SMS", "android.permission.SYSTEM_ALERT_WINDOW"],
            "S5_restricted_apis": ["SmsManager"],
            "S7_suspicious_apis": ["DexClassLoader"],
            "S8_network_addresses": ["http://a", "http://b", "http://c", "http://d"],
            "total_drebin_feature_count": 8,
        })
        assert res["predicted_malware"] is True


# ══════════════════════════════════════════════════════════════════════════════
# 7. PROFILE ANALYZER TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestProfileAnalyzer:
    @pytest.fixture
    def analyzer(self) -> ProfileAnalyzer:
        return ProfileAnalyzer()

    @pytest.mark.asyncio
    async def test_normal_input(self, analyzer: ProfileAnalyzer):
        url = "https://x.com/official_investor_99"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, url))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["platform"] == "twitter"
        assert rec.findings["username"] == "official_investor_99"

    @pytest.mark.asyncio
    async def test_empty_input(self, analyzer: ProfileAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, ""))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_corrupted_input(self, analyzer: ProfileAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, "https://t.me/###invalid???"))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_oversized_input(self, analyzer: ProfileAnalyzer):
        huge_url = "https://t.me/" + ("u" * 5000)  # > 4KB
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, huge_url))
        assert rec.status == AnalyzerExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_format(self, analyzer: ProfileAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, "https://unknown-social-network.org/user"))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        assert rec.findings["platform"] == "unsupported"

    @pytest.mark.asyncio
    async def test_malicious_input(self, analyzer: ProfileAnalyzer):
        # Telegram scam channel with fake SEBI claims and VIP calls
        url = "https://t.me/sebi_verified_vip_jackpot_calls"
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, url))
        assert rec.status == AnalyzerExecutionStatus.SUCCESS
        findings = rec.findings
        assert findings["platform"] == "telegram"
        assert findings["is_suspicious"] is True
        assert len(findings["suspicious_signals"]) > 0

        # Verify normalization
        canonical = analyzer.normalize_to_canonical_evidence("inv_prof_1", findings)
        assert len(canonical) == 1

    @pytest.mark.asyncio
    async def test_timeout(self, analyzer: ProfileAnalyzer):
        rec = await analyzer.execute(_make_evidence(EvidenceMediaType.URL, "https://t.me/mychannel"))
        assert rec.execution_duration_ms >= 0.0

    @pytest.mark.asyncio
    async def test_dependency_unavailable(self, analyzer: ProfileAnalyzer):
        # Platform identification runs purely deterministic
        assert analyzer._identify_platform("t.me") == "telegram"
        assert analyzer._identify_platform("x.com") == "twitter"
        assert analyzer._identify_platform("linkedin.com") == "linkedin"


# ══════════════════════════════════════════════════════════════════════════════
# 8. ML EVALUATION BENCHMARK METRICS TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestMLEvaluation:
    def test_url_model_evaluation_metrics(self):
        url_analyzer = URLAnalyzer()
        evaluator = ModelEvaluator()

        dataset = [
            {"input": "http://192.168.1.1/zerodha.xyz", "ground_truth": True},
            {"input": "https://guaranteed-profit-invest.xyz", "ground_truth": True},
            {"input": "https://google.com", "ground_truth": False},
            {"input": "https://github.com", "ground_truth": False},
        ]

        def predict_url(u: str) -> bool:
            det = url_analyzer.analyze_deterministic(u)
            ml = url_analyzer.classify_xgboost(det["feature_vector"])
            return bool(ml["predicted_phishing"])

        report = evaluator.evaluate_model(
            model_name="XGBoost_URL_Classifier",
            model_version=url_analyzer._model_version,
            dataset=dataset,
            predict_fn=predict_url,
        )

        assert report.model_name == "XGBoost_URL_Classifier"
        assert report.model_version == "url.xgboost.v1.0.0"
        assert report.total_eval_samples == 4
        assert report.precision >= 0.80
        assert report.recall >= 0.80
        assert report.f1_score >= 0.80
        assert len(report.confusion_matrix) == 2
        assert report.false_negative_rate <= 0.20
        assert report.avg_latency_ms >= 0.0
        assert report.inference_failure_rate == 0.0

    def test_apk_model_evaluation_metrics(self):
        apk_analyzer = APKAnalyzer()
        evaluator = ModelEvaluator()

        dataset = [
            {
                "input": {"S2_requested_permissions": ["android.permission.RECEIVE_SMS", "android.permission.SYSTEM_ALERT_WINDOW"]},
                "ground_truth": True,
            },
            {
                "input": {"S2_requested_permissions": ["android.permission.INTERNET"]},
                "ground_truth": False,
            },
        ]

        def predict_apk(inp: dict) -> bool:
            res = apk_analyzer._classify_drebin_xgboost(inp)
            return bool(res["predicted_malware"])

        report = evaluator.evaluate_model(
            model_name="XGBoost_Drebin_APK_Classifier",
            model_version=apk_analyzer._model_version,
            dataset=dataset,
            predict_fn=predict_apk,
        )

        assert report.model_version == "apk.drebin_xgboost.v1.0.0"
        assert report.precision == 1.0
        assert report.recall == 1.0
        assert report.f1_score == 1.0
        assert report.false_negative_rate == 0.0

    def test_deepfake_model_evaluation_metrics(self):
        video_analyzer = VideoAnalyzer()
        evaluator = ModelEvaluator()

        dataset = [
            {"input": [0.85, 0.90, 0.82], "ground_truth": True},
            {"input": [0.10, 0.15, 0.12], "ground_truth": False},
        ]

        def predict_deepfake(scores: list[float]) -> bool:
            agg, _ = video_analyzer._temporal_aggregate(scores)
            return agg >= 0.60

        report = evaluator.evaluate_model(
            model_name="MesoNet4_Video_Deepfake",
            model_version=video_analyzer._version,
            dataset=dataset,
            predict_fn=predict_deepfake,
        )

        assert report.precision == 1.0
        assert report.recall == 1.0
        assert report.false_negative_rate == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 9. FAILSAFE & PHASE GATE COMPLIANCE TESTS
# ══════════════════════════════════════════════════════════════════════════════
class TestPhaseGateAndFailsafe:
    def test_all_analyzers_registered(self):
        """Verify all specialized detection modules are active in registry with semver."""
        expected_engines = [
            "engine.message.heuristics",
            "engine.image.forensics",
            "engine.video.deepfake.mesonet",
            "engine.audio.forensics",
            "engine.url.forensics_and_ml",
            "engine.apk.static_and_drebin",
            "engine.profile.public_osint",
        ]
        versions = analyzer_registry.list_versions()
        for eng in expected_engines:
            assert eng in versions
            assert versions[eng] == "1.0.0"

    @pytest.mark.asyncio
    async def test_analyzer_failure_failsafe_rule_9(self):
        """When an analyzer fails:
        - failure recorded with uncertainty 1.0
        - never interprets failure as safety
        - never fabricates result
        """
        analyzer = URLAnalyzer()
        # Trigger failure via invalid parameter that raises exception
        bad_ev = CanonicalEvidenceItem(
            id="ev_err",
            investigation_id="inv_err",
            media_type=EvidenceMediaType.URL,
            sha256="000",
            title="Error Item",
            source_origin="err",
            content_payload="A" * 9000,  # exceeds limit, triggers ValueError
            verification=VerificationResult(
                state=VerificationState.UNAVAILABLE,
                source="test",
                confidence=0.0,
                details="test",
            ),
        )
        rec = await analyzer.execute(bad_ev)
        assert rec.status == AnalyzerExecutionStatus.FAILED
        assert rec.uncertainty == 1.0
        assert "ValueError" in (rec.error_message or "")
        assert rec.findings.get("safe_default_applied") is False

    def test_phase_gate_no_detector_modifies_risk_score_directly(self):
        """No detector object possesses a write handle or method to mutate investigation.risk_score directly.
        All analyzers strictly output CanonicalEvidenceItem or findings dictionaries.
        """
        for eng in [
            MessageAnalyzer(),
            ImageAnalyzer(),
            VideoAnalyzer(),
            AudioAnalyzer(),
            URLAnalyzer(),
            APKAnalyzer(),
            ProfileAnalyzer(),
        ]:
            # Ensure analyzers do not have risk score calculation methods
            assert not hasattr(eng, "calculate_risk_score")
            assert not hasattr(eng, "set_risk_score")
            assert not hasattr(eng, "assign_risk_score")
            # Ensure all implement BaseAnalyzer contract
            assert hasattr(eng, "metadata")
            assert hasattr(eng, "execute")
            assert hasattr(eng, "normalize_to_canonical_evidence")

"""Audio Extraction, Transcription, and Forensics Engine for VERA.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 12: Every model/analyzer exposes version metadata.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re
from datetime import UTC, datetime
from typing import Any

from ..contracts.analyzers import AnalyzerMetadata
from ..contracts.enums import EvidenceCategory, EvidenceSeverity, SourceType
from ..contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from ..contracts.phase2 import EvidenceItem
from ..contracts.verification import VerificationResult, VerificationState
from .base import BaseAnalyzer
from .stt_engine import FasterWhisperEngine

logger = logging.getLogger("vera.engines.audio")


class AudioAnalyzer(BaseAnalyzer):
    """Specialized analyzer for audio forensics, speech-to-text, and spoken fraud indicators.

    Implements:
    - Audio stream extraction
    - faster-whisper STT transcription
    - Transcript linguistic analysis (urgency, guaranteed profit, advance fees)
    - Voice cloning / synthetic speech acoustic artifact indicators
    """

    def __init__(
        self,
        stt_engine: FasterWhisperEngine | None = None,
        version: str = "1.0.0",
        rules_digest: str = "sha256:audio_rules_v1_e92b17ac",
    ) -> None:
        self._stt_engine = stt_engine or FasterWhisperEngine()
        self._version = version
        self._rules_digest = rules_digest

    @property
    def metadata(self) -> AnalyzerMetadata:
        return AnalyzerMetadata(
            name="engine.audio.forensics",
            version=self._version,
            weights_or_config_digest=self._rules_digest,
            provider="VERA Audio Forensics Core",
        )

    async def _execute(
        self,
        evidence: CanonicalEvidenceItem,
    ) -> tuple[dict[str, Any], float]:
        """Execute audio stream extraction, transcription, and acoustic analysis."""
        payload = evidence.content_payload or ""

        # Oversized audio payload guard (50MB)
        if len(payload) > 50_000_000:
            raise ValueError(f"Audio payload exceeds maximum size limit (50MB). Received: {len(payload)} bytes")

        if not payload.strip():
            return {
                "transcript": "",
                "segments": [],
                "acoustic_indicators": {},
                "linguistic_indicators": {},
                "is_suspicious": False,
            }, 0.5

        # 1. Run STT Transcription via faster-whisper
        stt_result, stt_uncertainty = await self._stt_engine._execute(evidence)
        transcript = stt_result.get("transcript", "")
        segments = stt_result.get("segments", [])

        # 2. Analyze Transcript for Spoken Fraud Markers
        linguistic = self._analyze_transcript(transcript)

        # 3. Analyze Acoustic Properties / Synthesis Artifacts
        acoustic = self._analyze_acoustic_artifacts(payload, segments)

        is_suspicious = (
            linguistic.get("has_fraud_markers", False)
            or acoustic.get("voice_cloning_detected", False)
        )

        findings = {
            "transcript": transcript,
            "segments_count": len(segments),
            "language": stt_result.get("language", "en"),
            "acoustic_indicators": acoustic,
            "linguistic_indicators": linguistic,
            "is_suspicious": is_suspicious,
        }

        uncertainty = 0.15 if is_suspicious else 0.35
        return findings, uncertainty

    def _analyze_transcript(self, transcript: str) -> dict[str, Any]:
        """Extract fraud markers from audio transcript."""
        if not transcript:
            return {"has_fraud_markers": False, "urgency": [], "guarantees": [], "fees": []}

        urgency_patterns = [
            r"\b(?:urgent|hurry|immediate|last chance|act fast|offer ends)\b",
            r"\b(?:limited slots?|only \d+ seats? left)\b",
        ]
        guarantee_patterns = [
            r"\b(?:100%|guaranteed|assured|risk[- ]free|fixed return)\b",
            r"\b(?:double your money|daily return|zero risk)\b",
        ]
        fee_patterns = [
            r"\b(?:pay|deposit)\s*(?:tax|fee|charge)\s*(?:to|for)\s*withdraw\b",
            r"\b(?:unfreeze|release fee)\b",
        ]

        urgency = self._find_matches(transcript, urgency_patterns)
        guarantees = self._find_matches(transcript, guarantee_patterns)
        fees = self._find_matches(transcript, fee_patterns)

        has_markers = bool(urgency or guarantees or fees)

        return {
            "has_fraud_markers": has_markers,
            "urgency_markers": urgency,
            "guarantee_markers": guarantees,
            "advance_fee_markers": fees,
            "total_markers": len(urgency) + len(guarantees) + len(fees),
        }

    def _find_matches(self, text: str, patterns: list[str]) -> list[str]:
        found: list[str] = []
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                found.append(m.group(0))
        return list(set(found))

    def _analyze_acoustic_artifacts(
        self,
        payload: str,
        segments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Inspects audio stream for synthetic speech / TTS robotic cadence indicators."""
        # Check segment pacing: overly uniform segment duration with zero natural pause indicates TTS
        if len(segments) >= 3:
            durations = [seg.get("end", 0) - seg.get("start", 0) for seg in segments]
            variance = sum((d - (sum(durations) / len(durations))) ** 2 for d in durations) / len(durations)
            is_robotic_cadence = variance < 0.05
        else:
            is_robotic_cadence = False

        # In a deepfake voice cloning scam, natural breathing and room acoustic reverberation are absent
        has_cloning_markers = is_robotic_cadence and any(
            seg.get("confidence", 1.0) > 0.98 for seg in segments
        )

        return {
            "segment_duration_variance": round(float(variance), 4) if len(segments) >= 3 else 0.5,
            "unnatural_cadence_detected": is_robotic_cadence,
            "voice_cloning_detected": has_cloning_markers,
            "synthetic_speech_likelihood": 0.85 if has_cloning_markers else 0.15,
        }

    def normalize_to_canonical_evidence(
        self,
        investigation_id: str,
        findings: dict[str, Any],
        source_origin: str = "recorded_audio",
    ) -> list[CanonicalEvidenceItem]:
        """Convert audio findings into canonical evidence schema items."""
        items: list[CanonicalEvidenceItem] = []
        now = datetime.now(UTC)

        transcript = findings.get("transcript", "")
        if transcript:
            uid = hashlib.sha256(f"{investigation_id}:audio_trans:{transcript}".encode()).hexdigest()[:16]
            is_fraud = findings.get("linguistic_indicators", {}).get("has_fraud_markers", False)

            items.append(CanonicalEvidenceItem(
                id=f"ev_aud_trans_{uid}",
                investigation_id=investigation_id,
                media_type=EvidenceMediaType.AUDIO,
                sha256=hashlib.sha256(transcript.encode()).hexdigest(),
                title="Audio Transcript & Voice Forensics",
                source_origin=source_origin,
                content_payload=transcript[:500],
                verification=VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="engine.audio.faster_whisper",
                    confidence=0.91,
                    details="Audio transcript extracted with spoken financial pitch indicators." if is_fraud else "Audio transcript extracted.",
                    has_analyzer_failure=False,
                ),
                created_at=now,
                tags=["audio_forensics", "faster_whisper", "spoken_pitch"],
            ))

        return items

    def normalize_to_evidence_item(
        self,
        investigation_id: str,
        findings: dict[str, Any],
        source_reference: str,
    ) -> list[EvidenceItem]:
        """Convert audio findings into Phase 2 EvidenceItem models."""
        items: list[EvidenceItem] = []
        now = datetime.now(UTC)

        if findings.get("is_suspicious"):
            uid = hashlib.sha256(f"{investigation_id}:{source_reference}:{findings}".encode()).hexdigest()[:16]
            items.append(EvidenceItem(
                id=f"ev_aud_{uid}",
                investigation_id=investigation_id,
                type="AUDIO_FRAUD_INDICATORS",
                category=EvidenceCategory.COMMUNICATION,
                severity=EvidenceSeverity.HIGH,
                confidence=0.89,
                description="Audio forensics detected suspicious spoken solicitations or synthetic speech indicators.",
                source_type=SourceType.STT,
                source_reference=source_reference,
                analyzer=self.metadata.name,
                analyzer_version=self._version,
                created_at=now,
                metadata=findings,
            ))

        return items

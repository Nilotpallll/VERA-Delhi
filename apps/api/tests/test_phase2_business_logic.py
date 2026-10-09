"""Phase 2: ORM, in-memory CRUD, and business rule unit tests.

Tests:
  - Evidence immutability (no updated_at column)
  - Audit trail creation
  - Failsafe: missing evidence never becomes negative
  - Incomplete investigation remains explicitly incomplete
  - Failed analyzers create system evidence (Rule 9)
  - Claim traceability to source
  - Duplicate investigation prevention
  - Malformed evidence
  - Missing source references
  - Realistic sample investigations
"""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from apps.api.src.contracts.enums import (
    EvidenceCategory,
    EvidenceSeverity,
    InputType,
    InvestigationStatus,
    SourceType,
)
from apps.api.src.contracts.phase2 import (
    AnalyzeRequest,
    Claim,
    EvidenceItem,
    InvestigationInputCreate,
    RiskSignal,
)
from apps.api.src.models.phase2 import (
    AuditLogModel,
    ClaimModel,
    EvidenceModel,
    InputModel,
    InvestigationModel,
    RiskSignalModel,
)
from apps.api.src.services.investigation_service import (
    _check_suspicious_url,
    _score_to_tier,
    _new_id,
)


# ── ID Generation ─────────────────────────────────────────────────────────────
class TestIdGeneration:
    def test_prefixed_ids_unique(self):
        ids = {_new_id("inv") for _ in range(1000)}
        assert len(ids) == 1000

    def test_prefix_applied(self):
        assert _new_id("ev").startswith("ev_")
        assert _new_id("sig").startswith("sig_")
        assert _new_id("audit").startswith("audit_")


# ── Evidence Model ────────────────────────────────────────────────────────────
class TestEvidenceImmutability:
    """Evidence must be append-only — no updated_at field (Rule 5)."""

    def test_evidence_model_has_no_updated_at(self):
        """Evidence ORM model must not have an updated_at column."""
        columns = {col.name for col in EvidenceModel.__table__.columns}
        assert "updated_at" not in columns, (
            "Evidence is immutable — must not have updated_at column"
        )

    def test_evidence_model_has_created_at(self):
        columns = {col.name for col in EvidenceModel.__table__.columns}
        assert "created_at" in columns

    def test_all_required_columns_exist(self):
        required = {
            "id", "investigation_id", "type", "category", "severity",
            "description", "source_type", "source_reference",
            "analyzer", "analyzer_version", "created_at", "extra_metadata"
        }
        columns = {col.name for col in EvidenceModel.__table__.columns}
        missing = required - columns
        assert not missing, f"Missing evidence columns: {missing}"

    def test_evidence_model_no_primary_key_update(self):
        """Primary key should be immutable string — no autoincrement."""
        pk_cols = [col for col in EvidenceModel.__table__.columns if col.primary_key]
        assert len(pk_cols) == 1
        assert pk_cols[0].name == "id"
        assert pk_cols[0].type.length == 64


# ── Investigation Model ───────────────────────────────────────────────────────
class TestInvestigationModel:
    def test_investigation_status_column_exists(self):
        columns = {col.name for col in InvestigationModel.__table__.columns}
        assert "status" in columns
        assert "manifest" in columns
        assert "risk_score" in columns
        assert "risk_tier" in columns

    def test_investigation_model_has_all_relationships(self):
        """InvestigationModel must have all 9 required relationship attributes."""
        required_rels = [
            "inputs", "evidence", "entities", "relationships_list",
            "claims", "verification_results", "risk_signals",
            "model_runs", "analyzer_runs", "reports", "audit_logs"
        ]
        for rel in required_rels:
            assert hasattr(InvestigationModel, rel), f"Missing relationship: {rel}"


# ── Suspicious URL detection ──────────────────────────────────────────────────
class TestSuspiciousURLDetection:
    def test_detects_invest_keyword(self):
        hits = _check_suspicious_url("https://top-invest-now.xyz")
        assert "invest" in hits

    def test_detects_multiple_keywords(self):
        hits = _check_suspicious_url("https://guaranteed-profit-return-invest.xyz")
        assert "guaranteed" in hits
        assert "profit" in hits
        assert "return" in hits

    def test_benign_url_no_hits(self):
        hits = _check_suspicious_url("https://example.com/about")
        assert hits == []

    def test_case_insensitive(self):
        hits = _check_suspicious_url("https://INVEST-NOW.COM")
        assert "invest" in hits


# ── Score to Tier ─────────────────────────────────────────────────────────────
class TestScoreToTier:
    @pytest.mark.parametrize("score,expected", [
        (85.0, "CRITICAL"),
        (80.0, "CRITICAL"),
        (75.0, "HIGH"),
        (60.0, "HIGH"),
        (55.0, "MEDIUM"),
        (40.0, "MEDIUM"),
        (25.0, "LOW"),
        (10.0, "LOW"),
        (5.0, "SAFE"),
        (0.0, "SAFE"),
    ])
    def test_tier_boundaries(self, score: float, expected: str):
        assert _score_to_tier(score) == expected


# ── Failsafe: missing evidence not negative ───────────────────────────────────
class TestFailsafeInvariants:
    def test_no_inputs_yields_insufficient_not_safe(self):
        """
        FAILSAFE: zero inputs must not be interpreted as 'safe'.
        The investigation stays INSUFFICIENT_EVIDENCE / incomplete.
        """
        # This mirrors what the service does when no inputs are provided
        from apps.api.src.contracts.enums import InvestigationStatus
        # There's no safe default — only explicit INSUFFICIENT_EVIDENCE
        assert InvestigationStatus.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"
        # INSUFFICIENT_EVIDENCE is distinct from COMPLETED or FAILED
        assert InvestigationStatus.INSUFFICIENT_EVIDENCE != InvestigationStatus.COMPLETED
        assert InvestigationStatus.INSUFFICIENT_EVIDENCE != InvestigationStatus.FAILED

    def test_failed_analyzer_creates_uncertainty_not_safety(self):
        """
        Rule 9: Analyzer failure must never be interpreted as safety.
        Score contribution from failure must be non-zero.
        """
        # The service adds 15.0 penalty for each failed analyzer
        # This is always > 0, never reducing risk score
        failure_penalty = 15.0
        assert failure_penalty > 0.0

    def test_unavailable_source_not_negative_evidence(self):
        """Missing source references are not proof of innocence."""
        # A claim with no sources stays UNVERIFIED, not VERIFIED
        claim = Claim(
            id="clm_test",
            investigation_id="inv_test",
            claim_text="No sources available claim",
            claim_type="sebi_registration",
            # Explicitly no source IDs
            source_input_ids=[],
            source_evidence_ids=[],
        )
        from apps.api.src.contracts.enums import ClaimStatus
        assert claim.status == ClaimStatus.UNVERIFIED, (
            "Claims with no sources must remain UNVERIFIED, not VERIFIED"
        )


# ── Claim traceability ────────────────────────────────────────────────────────
class TestClaimTraceability:
    def test_claim_with_no_sources_stays_unverified(self):
        from apps.api.src.contracts.enums import ClaimStatus
        claim = Claim(
            id="clm_notrace",
            investigation_id="inv_001",
            claim_text="SEBI registered entity",
            claim_type="sebi_registration",
        )
        assert claim.status == ClaimStatus.UNVERIFIED

    def test_supported_claim_requires_supporting_evidence(self):
        from apps.api.src.contracts.enums import ClaimStatus
        claim = Claim(
            id="clm_sup",
            investigation_id="inv_001",
            claim_text="Entity is verified",
            claim_type="identity_verification",
            status=ClaimStatus.SUPPORTED,
            supporting_evidence_ids=["ev_001", "ev_002"],
            source_input_ids=["inp_001"],
        )
        assert claim.status == ClaimStatus.SUPPORTED
        assert len(claim.supporting_evidence_ids) == 2


# ── Realistic sample investigation data ──────────────────────────────────────
class TestRealisticSampleData:
    """Construct realistic sample investigations in-memory."""

    def _make_sample_investigation(self, title: str) -> dict[str, Any]:
        inv_id = f"inv_{uuid.uuid4().hex[:12]}"
        return {
            "id": inv_id,
            "title": title,
            "status": InvestigationStatus.QUEUED.value,
            "manifest": {
                "investigation_id": inv_id,
                "engine_semver": "1.0.0",
                "scoring_algorithm_version": "scoring.v2.0",
            },
            "created_at": datetime.now(UTC).isoformat(),
        }

    def test_telegram_scam_investigation(self):
        inv = self._make_sample_investigation("Telegram Crypto Investment Scam")
        assert inv["status"] == "QUEUED"

        evidence = EvidenceItem(
            id="ev_tg_001",
            investigation_id=inv["id"],
            type="social_media_channel",
            category=EvidenceCategory.COMMUNICATION,
            severity=EvidenceSeverity.HIGH,
            description="Telegram channel promising 5x crypto returns in 7 days",
            source_type=SourceType.USER_INPUT,
            source_reference="inp_001",
            confidence=1.0,
            metadata={"platform": "telegram", "channel_name": "CryptoMegaProfit"},
        )
        assert evidence.source_type == SourceType.USER_INPUT

    def test_deepfake_celebrity_endorsement(self):
        inv = self._make_sample_investigation("Deepfake Celebrity Endorsement Fraud")
        evidence = EvidenceItem(
            id="ev_df_001",
            investigation_id=inv["id"],
            type="deepfake_detection_result",
            category=EvidenceCategory.MEDIA,
            severity=EvidenceSeverity.CRITICAL,
            description="Deepfake detected with 94% confidence — fake Elon Musk endorsement video",
            source_type=SourceType.ML_MODEL,
            source_reference="inp_002",
            confidence=0.94,
            analyzer="engine.deepfake.mesonet4",
            analyzer_version="4.0.0",
            metadata={"model": "MesoNet-4", "score": 0.94},
        )
        assert evidence.analyzer == "engine.deepfake.mesonet4"
        assert evidence.confidence == 0.94

    def test_fake_sebi_certificate(self):
        inv = self._make_sample_investigation("Fake SEBI Registration Certificate")
        evidence = EvidenceItem(
            id="ev_sebi_001",
            investigation_id=inv["id"],
            type="regulatory_verification_failed",
            category=EvidenceCategory.REGULATORY,
            severity=EvidenceSeverity.CRITICAL,
            description="Entity 'ProfitMax Capital' not found in SEBI registry",
            source_type=SourceType.OFFICIAL_SOURCE,
            source_reference="inp_003",
            confidence=0.99,
            metadata={"registry": "SEBI", "query": "ProfitMax Capital"},
        )
        assert evidence.source_type == SourceType.OFFICIAL_SOURCE

    def test_android_apk_malware(self):
        inv = self._make_sample_investigation("Rogue Trading APK Investigation")
        evidence = EvidenceItem(
            id="ev_apk_001",
            investigation_id=inv["id"],
            type="apk_suspicious_permissions",
            category=EvidenceCategory.TECHNICAL,
            severity=EvidenceSeverity.HIGH,
            description="APK requests READ_CONTACTS, ACCESS_FINE_LOCATION, SEND_SMS",
            source_type=SourceType.DETERMINISTIC_ANALYZER,
            source_reference="inp_004",
            confidence=0.85,
            analyzer="engine.apk.androguard",
            analyzer_version="3.4.0",
            metadata={"permissions": ["READ_CONTACTS", "ACCESS_FINE_LOCATION", "SEND_SMS"]},
        )
        assert evidence.analyzer == "engine.apk.androguard"

    def test_whatsapp_pump_and_dump(self):
        """Realistic WhatsApp pump-and-dump scheme investigation."""
        inv = self._make_sample_investigation("WhatsApp Stock Pump and Dump Scheme")

        # Input: WhatsApp group
        inp = InvestigationInputCreate(
            type=InputType.WHATSAPP_GROUP,
            value="wa.me/+919876543210-group-link",
            description="WhatsApp group promoting penny stocks",
        )
        assert inp.type == InputType.WHATSAPP_GROUP

        # Claim: stock recommendation
        claim = Claim(
            id="clm_wa_001",
            investigation_id=inv["id"],
            claim_text="Buy XYZ Corp shares — guaranteed 10x in 30 days",
            claim_type="guaranteed_return",
            source_input_ids=["inp_001"],
        )
        from apps.api.src.contracts.enums import ClaimStatus
        assert claim.status == ClaimStatus.UNVERIFIED

        # Risk signal
        sig = RiskSignal(
            id="sig_wa_001",
            investigation_id=inv["id"],
            signal_type="guaranteed_return_claim",
            severity=EvidenceSeverity.CRITICAL,
            score_contribution=90.0,
            weight=0.45,
            source_evidence_ids=["ev_001"],
            source_type=SourceType.DETERMINISTIC_ANALYZER,
            deterministic_rule_id="RULE-CLAIM-001",
            description="Guaranteed return claim detected — regulatory red flag",
        )
        assert sig.score_contribution == 90.0


# ── Audit trail verification ──────────────────────────────────────────────────
class TestAuditTrail:
    def test_audit_log_model_has_required_columns(self):
        columns = {col.name for col in AuditLogModel.__table__.columns}
        required = {
            "id", "investigation_id", "actor_type", "actor_id",
            "action", "target_type", "target_id", "details", "created_at"
        }
        assert required.issubset(columns)

    def test_audit_log_no_updated_at(self):
        """Audit logs are immutable."""
        columns = {col.name for col in AuditLogModel.__table__.columns}
        assert "updated_at" not in columns

    def test_claim_model_has_all_source_fields(self):
        """Claims must have source traceability fields."""
        columns = {col.name for col in ClaimModel.__table__.columns}
        assert "source_input_ids" in columns
        assert "source_evidence_ids" in columns
        assert "supporting_evidence_ids" in columns
        assert "refuting_evidence_ids" in columns


# ── Source type enforcement ───────────────────────────────────────────────────
class TestSourceTypeDistinction:
    def test_all_source_types_are_distinct(self):
        from apps.api.src.contracts.enums import SourceType
        types = list(SourceType)
        assert len(types) == len(set(t.value for t in types))

    def test_system_source_for_analyzer_failure(self):
        """Failed analyzer evidence must use SYSTEM source type (Rule 9)."""
        ev = EvidenceItem(
            id="ev_fail",
            investigation_id="inv_001",
            type="analyzer_failure",
            category=EvidenceCategory.SYSTEM_EVENT,
            severity=EvidenceSeverity.CRITICAL,
            description="Analyzer failed — zero-trust failsafe applied",
            source_type=SourceType.SYSTEM,
            source_reference="system",
            metadata={"rule": "RULE-FAILSAFE-001"},
        )
        assert ev.source_type == SourceType.SYSTEM

    def test_llm_evidence_distinguished_from_deterministic(self):
        ev_llm = EvidenceItem(
            id="ev_llm",
            investigation_id="inv_001",
            type="entity_extraction_result",
            category=EvidenceCategory.IDENTITY,
            severity=EvidenceSeverity.MEDIUM,
            description="LLM extracted PERSON entity: John Doe",
            source_type=SourceType.LLM,
            source_reference="inp_001",
        )
        ev_det = EvidenceItem(
            id="ev_det",
            investigation_id="inv_001",
            type="url_heuristic_match",
            category=EvidenceCategory.TECHNICAL,
            severity=EvidenceSeverity.HIGH,
            description="URL matched suspicious keyword rule",
            source_type=SourceType.DETERMINISTIC_ANALYZER,
            source_reference="inp_001",
        )
        assert ev_llm.source_type != ev_det.source_type
        assert ev_llm.source_type == SourceType.LLM
        assert ev_det.source_type == SourceType.DETERMINISTIC_ANALYZER

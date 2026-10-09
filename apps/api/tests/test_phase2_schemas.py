"""Phase 2: Schema validation tests.

Tests all enums, contract schemas, and field constraints.
"""

import pytest
from pydantic import ValidationError

from apps.api.src.contracts.enums import (
    ClaimStatus,
    EntityType,
    EvidenceCategory,
    EvidenceSeverity,
    InputType,
    InvestigationStatus,
    RelationshipType,
    ReportStatus,
    SourceType,
)
from apps.api.src.contracts.phase2 import (
    AnalyzeRequest,
    AnalyzerRun,
    AuditLog,
    Claim,
    Entity,
    EntityRelationship,
    EvidenceItem,
    InvestigationInput,
    InvestigationInputCreate,
    ModelRun,
    RiskSignal,
    UserRecord,
    VerificationResultRecord,
)
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from datetime import UTC, datetime


# ── Status enums ──────────────────────────────────────────────────────────────
class TestInvestigationStatus:
    def test_all_six_statuses_present(self):
        vals = set(s.value for s in InvestigationStatus)
        assert vals == {
            "QUEUED", "RUNNING", "PARTIAL",
            "COMPLETED", "FAILED", "INSUFFICIENT_EVIDENCE"
        }

    def test_status_is_str_enum(self):
        assert InvestigationStatus.QUEUED == "QUEUED"
        assert InvestigationStatus.INSUFFICIENT_EVIDENCE == "INSUFFICIENT_EVIDENCE"


class TestSourceType:
    def test_all_ten_source_types_present(self):
        vals = set(s.value for s in SourceType)
        expected = {
            "user_input", "llm", "ml_model", "ocr", "stt",
            "deterministic_analyzer", "official_source",
            "web_source", "database", "system"
        }
        assert vals == expected


class TestEntityType:
    def test_all_entity_types_present(self):
        vals = set(s.value for s in EntityType)
        expected = {
            "PERSON", "COMPANY", "PHONE", "EMAIL", "UPI",
            "DOMAIN", "URL", "PROFILE", "APK", "MESSAGE",
            "IMAGE", "VIDEO", "AUDIO"
        }
        assert vals == expected


class TestRelationshipType:
    def test_all_relationship_types_present(self):
        vals = set(s.value for s in RelationshipType)
        expected = {
            "OWNS", "CONTROLS", "PROMOTES", "ASSOCIATED_WITH", "IMPERSONATES",
            "COMMUNICATES_WITH", "HOSTS", "SENDS", "MENTIONED_IN", "LINKED_TO"
        }
        assert vals == expected


# ── Evidence schema ───────────────────────────────────────────────────────────
class TestEvidenceItemSchema:
    def _make_evidence(self, **kwargs) -> dict:
        defaults = {
            "id": "ev_001",
            "investigation_id": "inv_001",
            "type": "suspicious_url_pattern",
            "category": EvidenceCategory.TECHNICAL,
            "severity": EvidenceSeverity.HIGH,
            "description": "Suspicious URL detected",
            "source_type": SourceType.DETERMINISTIC_ANALYZER,
            "source_reference": "inp_001",
            "created_at": datetime.now(UTC),
            "metadata": {},
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_evidence_item(self):
        ev = EvidenceItem(**self._make_evidence())
        assert ev.id == "ev_001"
        assert ev.source_type == SourceType.DETERMINISTIC_ANALYZER
        assert ev.category == EvidenceCategory.TECHNICAL

    def test_confidence_must_be_zero_to_one(self):
        with pytest.raises(ValidationError):
            EvidenceItem(**self._make_evidence(confidence=1.5))

    def test_confidence_can_be_none(self):
        ev = EvidenceItem(**self._make_evidence(confidence=None))
        assert ev.confidence is None

    def test_all_required_fields_present(self):
        ev = EvidenceItem(**self._make_evidence(
            analyzer="engine.url.heuristic",
            analyzer_version="0.1.0",
            confidence=0.85,
        ))
        # Verify all Phase 2 required fields exist
        assert ev.id is not None
        assert ev.investigation_id is not None
        assert ev.type is not None
        assert ev.category is not None
        assert ev.severity is not None
        assert ev.description is not None
        assert ev.source_type is not None
        assert ev.source_reference is not None
        assert ev.analyzer == "engine.url.heuristic"
        assert ev.analyzer_version == "0.1.0"
        assert ev.created_at is not None
        assert ev.metadata is not None

    def test_missing_required_field_raises(self):
        data = self._make_evidence()
        del data["source_reference"]
        with pytest.raises(ValidationError):
            EvidenceItem(**data)


# ── Input schema ──────────────────────────────────────────────────────────────
class TestInvestigationInputSchema:
    def test_valid_url_input(self):
        inp = InvestigationInputCreate(
            type=InputType.URL,
            value="https://fake-invest.xyz",
            description="Reported URL",
            source_label="WhatsApp",
        )
        assert inp.type == InputType.URL
        assert inp.value == "https://fake-invest.xyz"

    def test_valid_phone_input(self):
        inp = InvestigationInputCreate(
            type=InputType.PHONE_NUMBER,
            value="+919876543210",
        )
        assert inp.type == InputType.PHONE_NUMBER

    def test_metadata_defaults_to_empty(self):
        inp = InvestigationInputCreate(type=InputType.TEXT, value="Some text")
        assert inp.metadata == {}

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            InvestigationInputCreate(value="test")


# ── Entity schema ─────────────────────────────────────────────────────────────
class TestEntitySchema:
    def test_valid_entity(self):
        entity = Entity(
            id="ent_001",
            investigation_id="inv_001",
            type=EntityType.DOMAIN,
            value="fake-invest.xyz",
            confidence=0.95,
            source_evidence_ids=["ev_001"],
            source_input_ids=["inp_001"],
        )
        assert entity.type == EntityType.DOMAIN
        assert entity.value == "fake-invest.xyz"

    def test_all_entity_types_valid(self):
        for et in EntityType:
            e = Entity(
                id=f"ent_{et.value}",
                investigation_id="inv_001",
                type=et,
                value=f"test_{et.value}",
            )
            assert e.type == et


# ── Relationship schema ───────────────────────────────────────────────────────
class TestRelationshipSchema:
    def test_typed_traceable_relationship(self):
        rel = EntityRelationship(
            id="rel_001",
            investigation_id="inv_001",
            source_entity_id="ent_001",
            target_entity_id="ent_002",
            relationship_type=RelationshipType.OWNS,
            confidence=0.90,
            evidence_ids=["ev_001", "ev_002"],
        )
        assert rel.relationship_type == RelationshipType.OWNS
        assert len(rel.evidence_ids) == 2


# ── Claim schema ──────────────────────────────────────────────────────────────
class TestClaimSchema:
    def test_claim_traceability_to_input(self):
        """Every claim must be traceable to input or evidence."""
        claim = Claim(
            id="clm_001",
            investigation_id="inv_001",
            claim_text="30% monthly returns guaranteed",
            claim_type="return_guarantee",
            status=ClaimStatus.UNVERIFIED,
            source_input_ids=["inp_001"],
        )
        assert claim.source_input_ids == ["inp_001"]
        assert claim.status == ClaimStatus.UNVERIFIED

    def test_claim_can_reference_evidence(self):
        claim = Claim(
            id="clm_002",
            investigation_id="inv_001",
            claim_text="SEBI registered broker",
            claim_type="sebi_registration",
            source_evidence_ids=["ev_001"],
        )
        assert claim.source_evidence_ids == ["ev_001"]


# ── Risk signal schema ────────────────────────────────────────────────────────
class TestRiskSignalSchema:
    def test_valid_risk_signal(self):
        sig = RiskSignal(
            id="sig_001",
            investigation_id="inv_001",
            signal_type="suspicious_url",
            severity=EvidenceSeverity.HIGH,
            score_contribution=60.0,
            weight=0.35,
            source_evidence_ids=["ev_001"],
            source_type=SourceType.DETERMINISTIC_ANALYZER,
            deterministic_rule_id="RULE-URL-001",
            description="Suspicious URL detected",
        )
        assert sig.score_contribution == 60.0
        assert sig.weight == 0.35
        assert sig.source_type == SourceType.DETERMINISTIC_ANALYZER

    def test_score_contribution_bounds(self):
        with pytest.raises(ValidationError):
            RiskSignal(
                id="sig_bad",
                investigation_id="inv_001",
                signal_type="test",
                severity=EvidenceSeverity.LOW,
                score_contribution=150.0,  # > 100
                weight=0.5,
                source_type=SourceType.SYSTEM,
                deterministic_rule_id="RULE-X",
                description="bad",
            )

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            RiskSignal(
                id="sig_bad2",
                investigation_id="inv_001",
                signal_type="test",
                severity=EvidenceSeverity.LOW,
                score_contribution=50.0,
                weight=1.5,  # > 1.0
                source_type=SourceType.SYSTEM,
                deterministic_rule_id="RULE-X",
                description="bad",
            )


# ── Analyze request schema ────────────────────────────────────────────────────
class TestAnalyzeRequest:
    def test_default_analyze_request(self):
        req = AnalyzeRequest()
        assert req.force_rerun is False
        assert req.analyzer_subset is None

    def test_subset_specified(self):
        req = AnalyzeRequest(analyzer_subset=["engine.url.heuristic"])
        assert "engine.url.heuristic" in req.analyzer_subset

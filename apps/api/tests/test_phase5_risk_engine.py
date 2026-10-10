"""Phase 5 Tests: Deterministic Risk Engine.

Tests:
- Deterministic rule tests
- Boundary tests (0 and 100)
- Score cap tests
- Contradictory evidence
- Unavailable analyzer failsafe
- Duplicate signals deduplication
- Ruleset versioning
- Separate dimensions assertion
- Phase Gate: Reproducibility from stored evidence and ruleset version
"""

from apps.api.src.investigator.risk_engine import (
    DEFAULT_RULESET_VERSION,
    DeterministicRiskEngine,
    InvestigationCompleteness,
    RiskLevel,
)


class TestDeterministicRiskEngine:
    """Deterministic rule validation and boundary verification."""

    def test_empty_evidence_insufficient_evidence_failsafe(self):
        """Rule 9: Insufficient evidence yields INSUFFICIENT_EVIDENCE completeness."""
        res = DeterministicRiskEngine.evaluate(evidence_items=[], verification_records=[])
        assert res.risk_score == 0.0
        assert res.risk_level == RiskLevel.INCONCLUSIVE
        assert res.investigation_completeness == InvestigationCompleteness.INSUFFICIENT_EVIDENCE
        assert res.verification_status == "UNAVAILABLE"

    def test_guaranteed_return_rule(self):
        """guaranteed_return adds exactly +15."""
        evidence = [{"type": "guaranteed_return", "source_reference": "msg_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 15.0
        assert res.risk_level == RiskLevel.LOW
        assert len(res.active_signals) == 1
        assert res.active_signals[0].signal_type == "guaranteed_return"

    def test_unverified_entity_rule(self):
        """unverified_entity adds exactly +25."""
        evidence = [{"type": "unverified_entity", "source_reference": "ent_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 25.0
        assert res.risk_level == RiskLevel.MODERATE

    def test_domain_mismatch_rule(self):
        """domain_mismatch adds exactly +20."""
        evidence = [{"type": "domain_mismatch", "source_reference": "dom_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 20.0
        assert res.risk_level == RiskLevel.LOW

    def test_payment_mismatch_rule(self):
        """payment_mismatch adds exactly +20."""
        evidence = [{"type": "payment_mismatch", "source_reference": "upi_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 20.0
        assert res.risk_level == RiskLevel.LOW

    def test_withdrawal_fee_rule(self):
        """withdrawal_fee adds exactly +20."""
        evidence = [{"type": "withdrawal_fee", "source_reference": "msg_2"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 20.0
        assert res.risk_level == RiskLevel.LOW

    def test_known_indicator_rule(self):
        """known_indicator adds exactly +25."""
        evidence = [{"type": "known_indicator", "source_reference": "phone_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 25.0
        assert res.risk_level == RiskLevel.MODERATE

    def test_suspicious_apk_rule(self):
        """suspicious_apk adds exactly +25."""
        evidence = [{"type": "suspicious_apk", "source_reference": "apk_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 25.0
        assert res.risk_level == RiskLevel.MODERATE

    def test_deepfake_signal_rule(self):
        """deepfake_signal adds exactly +25."""
        evidence = [{"type": "deepfake_signal", "source_reference": "vid_1"}]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 25.0
        assert res.risk_level == RiskLevel.MODERATE

    def test_score_cap_at_100_and_critical_tier(self):
        """Score must never exceed 100 even with many compounding adverse signals."""
        evidence = [
            {"type": "guaranteed_return", "source_reference": "s1"},    # 15
            {"type": "unverified_entity", "source_reference": "s2"},    # 25
            {"type": "domain_mismatch", "source_reference": "s3"},      # 20
            {"type": "payment_mismatch", "source_reference": "s4"},     # 20
            {"type": "withdrawal_fee", "source_reference": "s5"},       # 20
            {"type": "known_indicator", "source_reference": "s6"},      # 25
            {"type": "suspicious_apk", "source_reference": "s7"},       # 25
            {"type": "deepfake_signal", "source_reference": "s8"},      # 25
        ]
        # Sum = 175 -> Capped at 100.0
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 100.0
        assert res.risk_level == RiskLevel.CRITICAL
        assert len(res.active_signals) == 8

    def test_risk_bands(self):
        """Test boundary conditions for all 4 risk bands: LOW, MODERATE, HIGH, CRITICAL."""
        # 0–24: LOW (e.g. 20)
        res_low = DeterministicRiskEngine.evaluate(
            evidence_items=[{"type": "domain_mismatch", "source_reference": "r1"}]
        )
        assert res_low.risk_score == 20.0
        assert res_low.risk_level == RiskLevel.LOW

        # 25–49: MODERATE (e.g. 15 + 20 = 35)
        res_mod = DeterministicRiskEngine.evaluate(
            evidence_items=[
                {"type": "guaranteed_return", "source_reference": "r1"},
                {"type": "domain_mismatch", "source_reference": "r2"},
            ]
        )
        assert res_mod.risk_score == 35.0
        assert res_mod.risk_level == RiskLevel.MODERATE

        # 50–74: HIGH (e.g. 25 + 25 = 50)
        res_high = DeterministicRiskEngine.evaluate(
            evidence_items=[
                {"type": "unverified_entity", "source_reference": "r1"},
                {"type": "known_indicator", "source_reference": "r2"},
            ]
        )
        assert res_high.risk_score == 50.0
        assert res_high.risk_level == RiskLevel.HIGH

        # 75–100: CRITICAL (e.g. 25 + 25 + 25 = 75)
        res_crit = DeterministicRiskEngine.evaluate(
            evidence_items=[
                {"type": "unverified_entity", "source_reference": "r1"},
                {"type": "known_indicator", "source_reference": "r2"},
                {"type": "suspicious_apk", "source_reference": "r3"},
            ]
        )
        assert res_crit.risk_score == 75.0
        assert res_crit.risk_level == RiskLevel.CRITICAL

    def test_duplicate_signal_deduplication(self):
        """Identical signals from the exact same source reference must be deduplicated."""
        evidence = [
            {"type": "guaranteed_return", "source_reference": "msg_same"},
            {"type": "guaranteed_return", "source_reference": "msg_same"},
        ]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert res.risk_score == 15.0
        assert len(res.active_signals) == 1

    def test_contradictory_evidence_resolution(self):
        """Authentic VERIFIED record overrides unverified claim for the same entity."""
        evidence = [
            {
                "type": "unverified_entity",
                "source_reference": "Zerodha Broking Limited",
                "metadata": {"entity_name": "Zerodha Broking Limited"},
            }
        ]
        verifications = [
            {
                "entity_id": "Zerodha Broking Limited",
                "result": {"state": "VERIFIED", "details": "Found in SEBI register"},
            }
        ]
        res = DeterministicRiskEngine.evaluate(
            evidence_items=evidence, verification_records=verifications
        )
        # Contradicted: unverified signal is cancelled
        assert res.risk_score == 0.0
        assert res.risk_level == RiskLevel.LOW
        assert res.verification_status == "VERIFIED"

    def test_unavailable_analyzer_failsafe_rule_9(self):
        """When an analyzer is unavailable, investigation completeness must be PARTIAL."""
        evidence = [{"type": "domain_mismatch", "source_reference": "d1"}]
        res = DeterministicRiskEngine.evaluate(
            evidence_items=evidence, has_unavailable_analyzer=True
        )
        assert res.has_unavailable_analyzer is True
        assert res.investigation_completeness == InvestigationCompleteness.PARTIAL
        assert res.model_confidence <= 0.5

    def test_segregated_dimensions_invariant(self):
        """Model confidence, verification status, risk score, and completeness are strictly separate."""
        evidence = [
            {"type": "guaranteed_return", "source_reference": "m1", "confidence": 0.85}
        ]
        res = DeterministicRiskEngine.evaluate(evidence_items=evidence)
        assert isinstance(res.risk_score, float)
        assert isinstance(res.risk_level, RiskLevel)
        assert isinstance(res.investigation_completeness, InvestigationCompleteness)
        assert isinstance(res.model_confidence, float)
        assert isinstance(res.verification_status, str)
        # Risk score is NOT equal to model confidence
        assert res.risk_score == 15.0
        assert res.model_confidence == 0.85

    def test_ruleset_versioning(self):
        """Engine supports and exposes ruleset versions."""
        evidence = [{"type": "known_indicator", "source_reference": "k1"}]
        res = DeterministicRiskEngine.evaluate(
            evidence_items=evidence, ruleset_version=DEFAULT_RULESET_VERSION
        )
        assert res.ruleset_version == "rules.v2.0"

    def test_phase_gate_reproducibility(self):
        """PHASE GATE: Risk score must be 100% reproducible from stored evidence and ruleset version."""
        evidence = [
            {"type": "guaranteed_return", "source_reference": "s1"},
            {"type": "domain_mismatch", "source_reference": "s2"},
            {"type": "payment_mismatch", "source_reference": "s3"},
        ]
        verifications = [
            {"entity_id": "bad_actor", "result": {"state": "NOT_VERIFIED"}}
        ]

        run1 = DeterministicRiskEngine.evaluate(
            evidence_items=evidence,
            verification_records=verifications,
            ruleset_version="rules.v2.0",
        )
        run2 = DeterministicRiskEngine.evaluate(
            evidence_items=evidence,
            verification_records=verifications,
            ruleset_version="rules.v2.0",
        )

        assert run1.risk_score == run2.risk_score
        assert run1.risk_level == run2.risk_level
        assert len(run1.active_signals) == len(run2.active_signals)
        assert run1.summary == run2.summary

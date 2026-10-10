"""Phase 5 Evaluation: 8 Complete End-to-End Investigation Scenarios.

Scenarios:
1. benign investment message
2. guaranteed-return scam
3. fake SEBI representative
4. fake trading website
5. suspicious APK
6. manipulated investment video
7. mixed-evidence case
8. insufficient-evidence case
"""

import pytest
from apps.api.src.investigator.graph import VERAInvestigator
from apps.api.src.investigator.risk_engine import DeterministicRiskEngine
from apps.api.src.investigator.scenarios import EVALUATION_SCENARIOS


class TestPhase5EvaluationScenarios:
    """End-to-end scenario benchmark suite."""

    @pytest.mark.asyncio
    async def test_scenario_1_benign_investment_message(self):
        """Scenario 1: Legitimate broker with verified SEBI registration -> LOW risk."""
        sc = EVALUATION_SCENARIOS["benign_investment_message"]
        investigator = VERAInvestigator(max_iterations=2)
        res = await investigator.run_investigation(
            investigation_id="eval_sc1", inputs=sc["inputs"]
        )
        report = res.get("final_report", {})
        assert report.get("risk_level") == sc["expected"]["risk_level"]
        assert report.get("risk_score") <= sc["expected"]["max_score"]
        assert report.get("investigation_status") == sc["expected"]["status"]

        signal_types = [s["signal_type"] for s in report.get("suspicious_indicators", [])]
        for prohibited in sc["expected"]["signals_should_not_include"]:
            assert prohibited not in signal_types

    @pytest.mark.asyncio
    async def test_scenario_2_guaranteed_return_scam(self):
        """Scenario 2: WhatsApp guaranteed 3X profit scam with UPI payment -> HIGH/MODERATE risk."""
        sc = EVALUATION_SCENARIOS["guaranteed_return_scam"]
        investigator = VERAInvestigator(max_iterations=2)
        res = await investigator.run_investigation(
            investigation_id="eval_sc2", inputs=sc["inputs"]
        )
        report = res.get("final_report", {})
        assert report.get("risk_score") >= sc["expected"]["min_score"]
        assert report.get("investigation_status") == sc["expected"]["status"]

        signal_types = [s["signal_type"] for s in report.get("suspicious_indicators", [])]
        for req in sc["expected"]["signals_must_include"]:
            assert req in signal_types

    @pytest.mark.asyncio
    async def test_scenario_3_fake_sebi_representative(self):
        """Scenario 3: Fabricated SEBI registration number -> unverified_entity signal."""
        sc = EVALUATION_SCENARIOS["fake_sebi_representative"]
        investigator = VERAInvestigator(max_iterations=2)
        res = await investigator.run_investigation(
            investigation_id="eval_sc3", inputs=sc["inputs"]
        )
        report = res.get("final_report", {})
        assert report.get("risk_score") >= sc["expected"]["min_score"]
        assert report.get("investigation_status") == sc["expected"]["status"]

        signal_types = [s["signal_type"] for s in report.get("suspicious_indicators", [])]
        assert "unverified_entity" in signal_types

    @pytest.mark.asyncio
    async def test_scenario_4_fake_trading_website(self):
        """Scenario 4: Typosquatted .xyz domain impersonating broker -> domain_mismatch."""
        sc = EVALUATION_SCENARIOS["fake_trading_website"]
        investigator = VERAInvestigator(max_iterations=2)
        res = await investigator.run_investigation(
            investigation_id="eval_sc4", inputs=sc["inputs"]
        )
        report = res.get("final_report", {})
        assert report.get("risk_score") >= sc["expected"]["min_score"]
        assert report.get("investigation_status") == sc["expected"]["status"]

        signal_types = [s["signal_type"] for s in report.get("suspicious_indicators", [])]
        assert "domain_mismatch" in signal_types

    @pytest.mark.asyncio
    async def test_scenario_5_suspicious_apk(self):
        """Scenario 5: Rogue APK static analysis -> suspicious_apk signal."""
        sc = EVALUATION_SCENARIOS["suspicious_apk"]
        # Inject mock APK evidence to test risk attribution
        risk_res = DeterministicRiskEngine.evaluate(evidence_items=sc["mock_evidence"])
        assert risk_res.risk_score >= sc["expected"]["min_score"]
        signal_types = [s.signal_type for s in risk_res.active_signals]
        assert "suspicious_apk" in signal_types

    @pytest.mark.asyncio
    async def test_scenario_6_manipulated_investment_video(self):
        """Scenario 6: Deepfake endorsement video -> deepfake_signal."""
        sc = EVALUATION_SCENARIOS["manipulated_investment_video"]
        risk_res = DeterministicRiskEngine.evaluate(evidence_items=sc["mock_evidence"])
        assert risk_res.risk_score >= sc["expected"]["min_score"]
        signal_types = [s.signal_type for s in risk_res.active_signals]
        assert "deepfake_signal" in signal_types

    @pytest.mark.asyncio
    async def test_scenario_7_mixed_evidence_case(self):
        """Scenario 7: Multi-modal compound scam -> CRITICAL risk capped at 100."""
        sc = EVALUATION_SCENARIOS["mixed_evidence_case"]
        investigator = VERAInvestigator(max_iterations=2)
        res = await investigator.run_investigation(
            investigation_id="eval_sc7", inputs=sc["inputs"]
        )
        report = res.get("final_report", {})
        assert report.get("risk_level") == "CRITICAL"
        assert report.get("risk_score") >= sc["expected"]["min_score"]
        assert report.get("risk_score") <= sc["expected"]["score_cap"]
        assert report.get("investigation_status") == sc["expected"]["status"]

        signal_types = [s["signal_type"] for s in report.get("suspicious_indicators", [])]
        # Should include multiple compound signals
        assert "guaranteed_return" in signal_types
        assert "domain_mismatch" in signal_types
        assert "withdrawal_fee" in signal_types

    @pytest.mark.asyncio
    async def test_scenario_8_insufficient_evidence_case(self):
        """Scenario 8: Empty/ambiguous message -> INSUFFICIENT_EVIDENCE failsafe."""
        sc = EVALUATION_SCENARIOS["insufficient_evidence_case"]
        investigator = VERAInvestigator(max_iterations=1)
        res = await investigator.run_investigation(
            investigation_id="eval_sc8", inputs=sc["inputs"]
        )
        report = res.get("final_report", {})
        assert report.get("investigation_status") == sc["expected"]["status"]
        assert report.get("risk_score") == sc["expected"]["risk_score"]
        assert report.get("risk_level") == sc["expected"]["risk_level"]
        assert "INSUFFICIENT EVIDENCE" in report.get("executive_summary", "")

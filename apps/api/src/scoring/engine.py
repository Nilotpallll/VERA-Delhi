"""Deterministic Risk Scoring Engine.

Architecture Rule 6: Risk scoring is deterministic.
Architecture Rule 7: LLMs cannot directly assign final risk scores.
Architecture Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED and UNAVAILABLE.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
"""

from ..contracts.analyzers import AnalyzerExecutionRecord
from ..contracts.evidence import CanonicalEvidenceItem
from ..contracts.scoring import (
    DeterministicRiskAssessment,
    RiskSeverityTier,
    ScoreFactorContribution,
)
from ..contracts.verification import AnalyzerExecutionStatus, VerificationState


class DeterministicScoringEngine:
    ALGORITHM_VERSION = "scoring.v1.0"

    @classmethod
    def calculate_risk(
        cls,
        evidence_items: list[CanonicalEvidenceItem],
        analyzer_records: list[AnalyzerExecutionRecord],
    ) -> DeterministicRiskAssessment:
        factors: list[ScoreFactorContribution] = []
        uncertainty_penalty = 0.0

        # 1. Evaluate Registry & Authoritative Verification (Rule 8)
        for item in evidence_items:
            state = item.verification.state
            if state == VerificationState.NOT_VERIFIED:
                factors.append(
                    ScoreFactorContribution(
                        factor_id=f"reg_fail_{item.id}",
                        name=f"Unregistered / Failed Verification: {item.title}",
                        category="registry_check",
                        weight=0.35,
                        raw_score=95.0,
                        weighted_score=0.35 * 95.0,
                        reason="Claimed credentials or entities could not be corroborated in regulatory registries.",
                        deterministic_rule_id="RULE-REG-001-FAIL",
                    )
                )
            elif state == VerificationState.UNAVAILABLE:
                # Rule 8 & 9: UNAVAILABLE is not safe; it incurs ambiguity weight
                uncertainty_penalty += 15.0
                factors.append(
                    ScoreFactorContribution(
                        factor_id=f"reg_unavail_{item.id}",
                        name=f"Registry Verification Unavailable: {item.title}",
                        category="uncertainty_penalty",
                        weight=0.20,
                        raw_score=50.0,
                        weighted_score=0.20 * 50.0,
                        reason="Verification endpoint unavailable or timed out; cannot guarantee authenticity.",
                        deterministic_rule_id="RULE-REG-002-UNAVAILABLE",
                    )
                )
            elif state == VerificationState.VERIFIED:
                factors.append(
                    ScoreFactorContribution(
                        factor_id=f"reg_pass_{item.id}",
                        name=f"Verified Registry Match: {item.title}",
                        category="registry_check",
                        weight=0.30,
                        raw_score=5.0,
                        weighted_score=0.30 * 5.0,
                        reason="Entity positively verified against authoritative government/exchange registry.",
                        deterministic_rule_id="RULE-REG-003-VERIFIED",
                    )
                )

        # 2. Evaluate Analyzer Failures & Health (Rule 9)
        failed_analyzers = [
            r for r in analyzer_records if r.status in (AnalyzerExecutionStatus.FAILED, AnalyzerExecutionStatus.TIMED_OUT)
        ]
        if failed_analyzers:
            penalty_score = min(30.0, len(failed_analyzers) * 15.0)
            uncertainty_penalty += penalty_score
            factors.append(
                ScoreFactorContribution(
                    factor_id="analyzer_failure_penalty",
                    name="Inspection Degradation Uncertainty Penalty",
                    category="uncertainty_penalty",
                    weight=0.25,
                    raw_score=80.0,
                    weighted_score=0.25 * 80.0,
                    reason=f"{len(failed_analyzers)} inspection engines failed. Zero-trust invariant applied.",
                    deterministic_rule_id="RULE-FAILSAFE-001",
                )
            )

        # 3. Deterministic Aggregation
        total_weight = sum(f.weight for f in factors)
        if total_weight > 0:
            base_score = sum(f.weighted_score for f in factors) / total_weight
        else:
            base_score = 50.0 if not evidence_items else 20.0

        raw_final = base_score + (uncertainty_penalty * 0.25)
        final_score = round(max(0.0, min(100.0, raw_final)), 1)

        # 4. Severity Tier Assignment
        if failed_analyzers and not factors:
            tier = RiskSeverityTier.INCONCLUSIVE
        elif final_score >= 80.0:
            tier = RiskSeverityTier.CRITICAL
        elif final_score >= 60.0:
            tier = RiskSeverityTier.HIGH
        elif final_score >= 40.0:
            tier = RiskSeverityTier.MEDIUM
        elif final_score >= 10.0:
            tier = RiskSeverityTier.LOW
        else:
            tier = RiskSeverityTier.SAFE

        summary = (
            f"Deterministic evaluation computed risk score {final_score}/100 ({tier.value}). "
            f"Evaluated {len(factors)} active factors with {uncertainty_penalty:.1f} uncertainty penalty."
        )

        return DeterministicRiskAssessment(
            final_score=final_score,
            tier=tier,
            factors=factors,
            uncertainty_penalty=round(uncertainty_penalty, 1),
            algorithm_version=cls.ALGORITHM_VERSION,
            summary=summary,
            is_llm_assigned=False,  # Enforcing Rule 7
        )

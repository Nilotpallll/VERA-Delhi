"""Forensic Report Generator for VERA Investigator.

Architecture Rule 13: Investigations must be reproducible.
Rule: Zero chain-of-thought exposure in final report.
Rule: All SEBI citations must have source references.
"""

from datetime import UTC, datetime
from typing import Any

from .risk_engine import InvestigationCompleteness, RiskAssessmentResult, RiskLevel


class ForensicReportGenerator:
    """Produces the auditable, comprehensive final investigation report."""

    @classmethod
    def generate(
        cls,
        *,
        investigation_id: str,
        risk_assessment: RiskAssessmentResult,
        entities: list[dict[str, Any]],
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        verification_records: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        scam_lifecycle_stage: str = "unknown",
        missing_evidence: list[str] | None = None,
    ) -> dict[str, Any]:
        missing_evidence = missing_evidence or []
        suspicious_indicators = [
            {
                "signal_type": s.signal_type,
                "weight": s.weight,
                "description": s.description,
                "source": s.source_reference,
            }
            for s in risk_assessment.active_signals
        ]

        # Generate recommended actions based on risk level and detected signals
        recommended_actions = cls._generate_recommendations(risk_assessment, suspicious_indicators)

        # Build executive summary (no chain of thought)
        exec_summary = cls._build_executive_summary(
            risk_assessment=risk_assessment,
            entity_count=len(entities),
            claim_count=len(claims),
            indicator_count=len(suspicious_indicators),
            stage=scam_lifecycle_stage,
        )

        return {
            "investigation_id": investigation_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "executive_summary": exec_summary,
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level.value,
            "investigation_status": risk_assessment.investigation_completeness.value,
            "model_confidence": risk_assessment.model_confidence,
            "detected_entities": entities,
            "claims": claims,
            "evidence": evidence,
            "verification_results": verification_records,
            "sebi_guidance_matches": citations,
            "suspicious_indicators": suspicious_indicators,
            "scam_lifecycle_stage": scam_lifecycle_stage,
            "missing_evidence": missing_evidence,
            "recommended_actions": recommended_actions,
            "source_citations": citations,
            "disclaimer": "These risk scores are prototype heuristic weights, NOT probabilities of fraud.",
            "ruleset_version": risk_assessment.ruleset_version,
        }

    @classmethod
    def _build_executive_summary(
        cls,
        risk_assessment: RiskAssessmentResult,
        entity_count: int,
        claim_count: int,
        indicator_count: int,
        stage: str,
    ) -> str:
        if risk_assessment.investigation_completeness == InvestigationCompleteness.INSUFFICIENT_EVIDENCE:
            return (
                "Investigation concluded with INSUFFICIENT EVIDENCE. Submitted materials "
                "lack verifiable indicators, regulatory claims, or technical artifacts. "
                "No definitive risk attribution could be determined safely."
            )

        if risk_assessment.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            return (
                f"Forensic analysis concluded with a {risk_assessment.risk_level.value} RISK rating "
                f"({risk_assessment.risk_score:.0f}/100). Found {indicator_count} adverse risk signals "
                f"across {entity_count} entities and {claim_count} claims. "
                f"Current scam lifecycle stage identified as '{stage}'. Immediate protective action advised."
            )
        elif risk_assessment.risk_level == RiskLevel.MODERATE:
            return (
                f"Forensic analysis concluded with a MODERATE RISK rating ({risk_assessment.risk_score:.0f}/100). "
                f"Detected {indicator_count} cautionary signals requiring scrutiny prior to financial engagement."
            )
        else:
            return (
                f"Forensic analysis concluded with a LOW RISK rating ({risk_assessment.risk_score:.0f}/100). "
                f"No deceptive solicitation, high-risk promises, or credential mismatches were detected."
            )

    @classmethod
    def _generate_recommendations(
        cls, risk_assessment: RiskAssessmentResult, indicators: list[dict[str, Any]]
    ) -> list[str]:
        recommendations = []
        if risk_assessment.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            recommendations.append("DO NOT TRANSFER FUNDS or share OTPs / banking credentials.")
            recommendations.append("DO NOT INSTALL or execute non-Play Store application packages (APKs).")
            recommendations.append("REPORT communication to the National Cyber Crime Reporting Portal (cybercrime.gov.in) and SEBI SCORES.")
        elif risk_assessment.risk_level == RiskLevel.MODERATE:
            recommendations.append("VERIFY regulatory registration number directly on https://www.sebi.gov.in before acting.")
            recommendations.append("Refrain from acting on time-pressured investment tips or private VIP groups.")
        else:
            recommendations.append("Maintain standard digital financial safety protocols.")

        signals = {i["signal_type"] for i in indicators}
        if "suspicious_apk" in signals:
            recommendations.append("Uninstall any downloaded APK immediately and run an antivirus scan.")
        if "payment_mismatch" in signals:
            recommendations.append("Do not make payments to personal UPI accounts for commercial investments.")

        return recommendations

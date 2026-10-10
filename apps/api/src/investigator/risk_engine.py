"""Deterministic Risk Engine for VERA Investigator.

Architecture Rule 6: Risk scoring is deterministic.
Architecture Rule 7: LLMs cannot directly assign final risk scores.
Architecture Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED, and UNAVAILABLE.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
Architecture Rule 13: Investigations must be reproducible.

NOTICE: These risk scores are prototype heuristic weights, NOT probabilities of fraud.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RiskLevel(StrEnum):
    LOW = "LOW"            # 0–24
    MODERATE = "MODERATE"  # 25–49
    HIGH = "HIGH"          # 50–74
    CRITICAL = "CRITICAL"  # 75–100
    INCONCLUSIVE = "INCONCLUSIVE"


class InvestigationCompleteness(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class RiskRule:
    """Immutable definition of a deterministic risk rule."""
    rule_id: str
    signal_type: str
    weight: float
    description: str
    category: str


# ── Standard Rule Catalog (Versioned) ─────────────────────────────────────────
DEFAULT_RULESET_VERSION = "rules.v2.0"

RULESET_REGISTRY: dict[str, dict[str, RiskRule]] = {
    "rules.v2.0": {
        "guaranteed_return": RiskRule(
            rule_id="RULE-GRTN-01",
            signal_type="guaranteed_return",
            weight=15.0,
            description="Assured profit or zero-risk return claims detected.",
            category="claim_risk",
        ),
        "unverified_entity": RiskRule(
            rule_id="RULE-UNVER-01",
            signal_type="unverified_entity",
            weight=25.0,
            description="Claimed regulatory intermediary or corporate entity could not be verified in official registry.",
            category="verification_risk",
        ),
        "domain_mismatch": RiskRule(
            rule_id="RULE-DOM-01",
            signal_type="domain_mismatch",
            weight=20.0,
            description="Domain is typosquatted, impersonating authentic institution, or using high-risk suspicious TLD.",
            category="technical_risk",
        ),
        "payment_mismatch": RiskRule(
            rule_id="RULE-PAY-01",
            signal_type="payment_mismatch",
            weight=20.0,
            description="Payment directed to third-party or individual UPI account for purported corporate investment.",
            category="financial_risk",
        ),
        "withdrawal_fee": RiskRule(
            rule_id="RULE-WDFEE-01",
            signal_type="withdrawal_fee",
            weight=20.0,
            description="Advance fee, tax release fee, or processing deposit required before funds can be withdrawn.",
            category="financial_risk",
        ),
        "known_indicator": RiskRule(
            rule_id="RULE-KNOWN-01",
            signal_type="known_indicator",
            weight=25.0,
            description="Entity, domain, UPI, or handle matches known fraudulent indicator or official alert list.",
            category="threat_intelligence",
        ),
        "suspicious_apk": RiskRule(
            rule_id="RULE-APK-01",
            signal_type="suspicious_apk",
            weight=25.0,
            description="APK contains dangerous permissions (SMS/overlay), debug certificate, or malicious API patterns.",
            category="technical_risk",
        ),
        "deepfake_signal": RiskRule(
            rule_id="RULE-DEEPFAKE-01",
            signal_type="deepfake_signal",
            weight=25.0,
            description="Media exhibits facial manipulation markers or synthetic audio acoustic artifacts.",
            category="media_forensics",
        ),
    }
}


@dataclass
class ComputedSignal:
    signal_type: str
    rule_id: str
    weight: float
    description: str
    source_reference: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessmentResult:
    """Comprehensive, segregated risk calculation output.

    KEEP SEPARATE:
    1. model_confidence (0.0 to 1.0)
    2. verification_status (tri-state summary)
    3. risk_score (0.0 to 100.0)
    4. investigation_completeness (COMPLETED / PARTIAL / INSUFFICIENT_EVIDENCE)
    """
    risk_score: float
    risk_level: RiskLevel
    investigation_completeness: InvestigationCompleteness
    model_confidence: float
    verification_status: str  # VERIFIED | NOT_VERIFIED | UNAVAILABLE | MIXED
    active_signals: list[ComputedSignal]
    ruleset_version: str
    has_unavailable_analyzer: bool
    summary: str


class DeterministicRiskEngine:
    """Stateless, deterministic risk calculation engine."""

    @classmethod
    def evaluate(
        cls,
        *,
        evidence_items: list[dict[str, Any]],
        verification_records: list[dict[str, Any]] | None = None,
        ruleset_version: str = DEFAULT_RULESET_VERSION,
        has_unavailable_analyzer: bool = False,
    ) -> RiskAssessmentResult:
        """Calculate deterministic risk score from evidence items and verification records.

        Reproducibility Guarantee: Given identical inputs and ruleset version,
        this method produces the EXACT same output every time.
        """
        ruleset = RULESET_REGISTRY.get(ruleset_version)
        if not ruleset:
            ruleset = RULESET_REGISTRY[DEFAULT_RULESET_VERSION]
            ruleset_version = DEFAULT_RULESET_VERSION

        verification_records = verification_records or []

        # ── 1. Check for Insufficient Evidence ────────────────────────────────
        if not evidence_items and not verification_records:
            return RiskAssessmentResult(
                risk_score=0.0,
                risk_level=RiskLevel.INCONCLUSIVE,
                investigation_completeness=InvestigationCompleteness.INSUFFICIENT_EVIDENCE,
                model_confidence=0.0,
                verification_status="UNAVAILABLE",
                active_signals=[],
                ruleset_version=ruleset_version,
                has_unavailable_analyzer=has_unavailable_analyzer,
                summary="Insufficient evidence to evaluate risk. Investigation cannot be concluded.",
            )

        # ── 2. Track Verification States & Resolve Contradictions ─────────────
        verified_entities = set()
        not_verified_entities = set()
        unavailable_verifications = set()

        for vr in verification_records:
            result = vr.get("result", {})
            state = result.get("state") if isinstance(result, dict) else getattr(result, "state", None)
            target = vr.get("entity_id") or vr.get("claim_id") or vr.get("metadata", {}).get("target", "unknown")
            if state == "VERIFIED":
                verified_entities.add(target)
            elif state == "NOT_VERIFIED":
                not_verified_entities.add(target)
            elif state == "UNAVAILABLE":
                unavailable_verifications.add(target)

        # Resolve contradictory evidence: Official VERIFIED overrides unverified claim for same target
        active_not_verified = not_verified_entities - verified_entities

        if verified_entities and not active_not_verified and not unavailable_verifications:
            overall_verif = "VERIFIED"
        elif active_not_verified:
            overall_verif = "NOT_VERIFIED"
        elif unavailable_verifications:
            overall_verif = "UNAVAILABLE"
        else:
            overall_verif = "MIXED"

        # ── 3. Extract & Deduplicate Signals ──────────────────────────────────
        active_signals: list[ComputedSignal] = []
        seen_signal_keys: set[str] = set()

        for ev in evidence_items:
            ev_type = ev.get("type", "")
            source_ref = ev.get("source_reference", "")
            meta = ev.get("metadata", {})
            signal_key = f"{ev_type}:{source_ref}"

            # Deduplication: skip identical signal from identical source
            if signal_key in seen_signal_keys:
                continue

            matched_rule = None
            if ev_type in ruleset:
                matched_rule = ruleset[ev_type]
            else:
                # Check metadata or alternate tags
                for rule_name, rule in ruleset.items():
                    if meta.get("signal_type") == rule_name or rule_name in ev_type:
                        matched_rule = rule
                        break

            if matched_rule:
                # If this is unverified_entity, check if it was contradicted by official verification
                if matched_rule.signal_type == "unverified_entity":
                    target = meta.get("entity_name") or source_ref
                    if target in verified_entities:
                        # Contradicted by authentic verification — do not fire unverified signal
                        continue

                seen_signal_keys.add(signal_key)
                active_signals.append(
                    ComputedSignal(
                        signal_type=matched_rule.signal_type,
                        rule_id=matched_rule.rule_id,
                        weight=matched_rule.weight,
                        description=matched_rule.description,
                        source_reference=source_ref,
                        metadata=meta,
                    )
                )

        # ── 4. Process Verification Records as Signals ────────────────────────
        for unverified_target in active_not_verified:
            sig_key = f"unverified_entity:{unverified_target}"
            if sig_key not in seen_signal_keys and "unverified_entity" in ruleset:
                rule = ruleset["unverified_entity"]
                seen_signal_keys.add(sig_key)
                active_signals.append(
                    ComputedSignal(
                        signal_type=rule.signal_type,
                        rule_id=rule.rule_id,
                        weight=rule.weight,
                        description=f"Entity {unverified_target} failed regulatory/official verification.",
                        source_reference=str(unverified_target),
                        metadata={"target": unverified_target},
                    )
                )

        # ── 5. Calculate Score & Apply Cap ────────────────────────────────────
        raw_score = sum(s.weight for s in active_signals)
        capped_score = min(100.0, max(0.0, raw_score))

        # ── 6. Determine Risk Level Band ──────────────────────────────────────
        # Bands: 0–24 LOW, 25–49 MODERATE, 50–74 HIGH, 75–100 CRITICAL
        if capped_score >= 75.0:
            level = RiskLevel.CRITICAL
        elif capped_score >= 50.0:
            level = RiskLevel.HIGH
        elif capped_score >= 25.0:
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.LOW

        # ── 7. Determine Investigation Completeness (Failsafe) ────────────────
        if has_unavailable_analyzer or unavailable_verifications:
            completeness = InvestigationCompleteness.PARTIAL
        else:
            completeness = InvestigationCompleteness.COMPLETED

        # ── 8. Calculate Model Confidence (Kept Strictly Separate) ────────────
        # Model confidence reflects sensor certainty, not probability of scam
        confidences = [
            ev.get("confidence", 1.0)
            for ev in evidence_items
            if ev.get("confidence") is not None
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0
        if has_unavailable_analyzer:
            avg_confidence = min(avg_confidence, 0.5)

        summary = (
            f"Evaluated {len(active_signals)} deterministic signals. "
            f"Deterministic score: {capped_score:.1f}/100 ({level.value}). "
            f"Notice: Prototype heuristic weights, NOT probabilities of fraud."
        )

        return RiskAssessmentResult(
            risk_score=capped_score,
            risk_level=level,
            investigation_completeness=completeness,
            model_confidence=avg_confidence,
            verification_status=overall_verif,
            active_signals=active_signals,
            ruleset_version=ruleset_version,
            has_unavailable_analyzer=has_unavailable_analyzer,
            summary=summary,
        )

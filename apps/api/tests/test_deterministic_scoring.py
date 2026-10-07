"""Test deterministic risk scoring engine rules.

Architecture Rule 6: Risk scoring is deterministic.
Architecture Rule 7: LLMs cannot directly assign final risk scores.
Architecture Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED and UNAVAILABLE.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
"""

from datetime import UTC, datetime

from apps.api.src.contracts.analyzers import AnalyzerExecutionRecord, AnalyzerMetadata
from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.scoring import RiskSeverityTier
from apps.api.src.contracts.verification import (
    AnalyzerExecutionStatus,
    VerificationResult,
    VerificationState,
)
from apps.api.src.scoring.engine import DeterministicScoringEngine


def _make_evidence(item_id: str, state: VerificationState) -> CanonicalEvidenceItem:
    return CanonicalEvidenceItem(
        id=item_id,
        investigation_id="inv_test",
        media_type=EvidenceMediaType.TEXT,
        sha256="fake_hash",
        title=f"Evidence {item_id}",
        source_origin="test",
        verification=VerificationResult(
            state=state,
            source="registry",
            confidence=1.0,
            details=f"Test verification {state}",
            has_analyzer_failure=False,
        ),
        created_at=datetime.now(UTC),
    )


def test_scoring_determinism_rule_6():
    """Identical evidence input MUST produce byte-for-byte identical output scores."""
    evidence = [_make_evidence("ev1", VerificationState.NOT_VERIFIED)]

    result_1 = DeterministicScoringEngine.calculate_risk(evidence, [])
    result_2 = DeterministicScoringEngine.calculate_risk(evidence, [])

    assert result_1.final_score == result_2.final_score
    assert result_1.tier == result_2.tier
    assert len(result_1.factors) == len(result_2.factors)
    assert result_1.final_score >= 80.0
    assert result_1.tier == RiskSeverityTier.CRITICAL


def test_llm_cannot_assign_risk_score_rule_7():
    """Architecture Rule 7: LLMs cannot directly assign final risk scores."""
    evidence = [_make_evidence("ev1", VerificationState.VERIFIED)]
    result = DeterministicScoringEngine.calculate_risk(evidence, [])

    # Contractual invariant: is_llm_assigned must be False
    assert result.is_llm_assigned is False
    assert result.tier == RiskSeverityTier.SAFE


def test_analyzer_failure_is_never_safe_rule_9():
    """Architecture Rule 9: Analyzer failure must never be interpreted as safety."""
    evidence = [_make_evidence("ev1", VerificationState.UNAVAILABLE)]
    failed_record = AnalyzerExecutionRecord(
        metadata=AnalyzerMetadata(
            name="engine.deepfake.mesonet",
            version="1.0.0",
            weights_or_config_digest="mesonet_weights_hash",
            provider="vera_ml",
        ),
        status=AnalyzerExecutionStatus.FAILED,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        execution_duration_ms=150.0,
        error_message="GPU memory exhausted / OCR service unreachable",
        uncertainty=1.0,
    )

    result = DeterministicScoringEngine.calculate_risk(evidence, [failed_record])

    # Uncertainty penalty must be applied; score must NOT be 0 (safe)
    assert result.uncertainty_penalty > 0.0
    assert result.final_score > 30.0
    assert result.tier != RiskSeverityTier.SAFE

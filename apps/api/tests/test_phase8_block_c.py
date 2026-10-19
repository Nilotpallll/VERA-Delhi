"""Tests for Phase 8 Block C: Detection Quality, Evaluation Harness, and Registry Invariants."""

from unittest.mock import patch

import httpx
import pytest
from apps.api.src.contracts.verification import VerificationState
from apps.api.src.evaluation.benchmark import run_benchmark, verify_thresholds_or_fail
from apps.api.src.services.registry_verification import registry_service


def test_benchmark_evaluation_harness_thresholds():
    """Benchmark evaluation over 350 labeled items meets minimum precision, recall, and F1 thresholds."""
    results = run_benchmark("data/eval/labeled_eval_set_300.json")

    assert "overall" in results
    overall = results["overall"]
    assert overall.total_samples >= 300

    # Minimum thresholds
    assert overall.recall >= 0.85, f"Recall was {overall.recall}"
    assert overall.precision >= 0.80, f"Precision was {overall.precision}"
    assert overall.f1 >= 0.82, f"F1 was {overall.f1}"

    # Verify thresholds validator passes without assertion error
    verify_thresholds_or_fail(results)

    # Check confusion matrix format
    matrix = overall.confusion_matrix
    assert len(matrix) == 2
    assert len(matrix[0]) == 2


@pytest.mark.asyncio
async def test_sebi_registry_outage_returns_unavailable_never_verified():
    """On connection outage or HTTP 500, SEBI lookup must return UNAVAILABLE, never VERIFIED or SAFE."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("SEBI gateway timeout")):
        result = await registry_service.verify_sebi_registration("INZ000123456")
        assert result.state == VerificationState.UNAVAILABLE
        assert result.state != VerificationState.VERIFIED
        assert "unreachable" in result.details.lower() or "unavailable" in result.details.lower()
        assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_mca21_registry_outage_returns_unavailable():
    """On MCA21 portal outage, return UNAVAILABLE."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        result = await registry_service.verify_mca_cin("U72200DL2020PTC123456")
        assert result.state == VerificationState.UNAVAILABLE
        assert result.state != VerificationState.VERIFIED


@pytest.mark.asyncio
async def test_icann_rdap_outage_returns_unavailable():
    """On ICANN RDAP registry outage, return UNAVAILABLE."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.ReadTimeout("RDAP timeout")):
        result = await registry_service.verify_icann_domain("zerodha-scam.xyz")
        assert result.state == VerificationState.UNAVAILABLE
        assert result.state != VerificationState.VERIFIED

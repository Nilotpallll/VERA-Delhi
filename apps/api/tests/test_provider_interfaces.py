"""Test AI provider interfaces and analyzer metadata exposure.

Architecture Rule 3: Models are accessed through provider interfaces.
Architecture Rule 12: Every model/analyzer must expose version metadata.
Architecture Rule 13: Every investigation must be reproducible from stored versions/configuration.
"""

from datetime import UTC, datetime
from typing import Any

import pytest
from apps.api.src.ai.base import LLMProvider
from apps.api.src.ai.gemini import GeminiProvider
from apps.api.src.ai.groq import GroqProvider
from apps.api.src.ai.ollama import OllamaProvider
from apps.api.src.contracts.analyzers import AnalyzerMetadata
from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import (
    AnalyzerExecutionStatus,
    VerificationResult,
    VerificationState,
)
from apps.api.src.engines.base import BaseAnalyzer
from apps.api.src.engines.registry import AnalyzerRegistry


def test_llm_provider_interface_conformance_rule_3():
    """All providers must conform to the LLMProvider abstract interface."""
    gemini = GeminiProvider(api_key="test_key")
    ollama = OllamaProvider(base_url="http://localhost:11434")
    groq = GroqProvider(api_key="test_key")

    for provider in (gemini, ollama, groq):
        assert isinstance(provider, LLMProvider)
        assert isinstance(provider.provider_name, str)
        assert isinstance(provider.model_name, str)


class MockFlakyAnalyzer(BaseAnalyzer):
    @property
    def metadata(self) -> AnalyzerMetadata:
        return AnalyzerMetadata(
            name="engine.mock.flaky",
            version="0.1.0",
            weights_or_config_digest="digest_12345",
            provider="test_team",
        )

    async def _execute(self, evidence: CanonicalEvidenceItem) -> tuple[dict[str, Any], float]:
        raise TimeoutError("Simulated analyzer crash")


@pytest.mark.asyncio
async def test_analyzer_version_exposure_and_failsafe_rule_12_and_9():
    """Analyzer must expose version metadata and handle failures without breaking contract."""
    analyzer = MockFlakyAnalyzer()
    assert analyzer.metadata.name == "engine.mock.flaky"
    assert analyzer.metadata.version == "0.1.0"
    assert analyzer.metadata.weights_or_config_digest == "digest_12345"

    evidence = CanonicalEvidenceItem(
        id="ev_test",
        investigation_id="inv_test",
        media_type=EvidenceMediaType.TEXT,
        sha256="hash",
        title="Sample",
        source_origin="origin",
        verification=VerificationResult(
            state=VerificationState.UNAVAILABLE,
            source="none",
            confidence=0.0,
            details="none",
            has_analyzer_failure=False,
        ),
        created_at=datetime.now(UTC),
    )

    # Safe execution harness must catch exception and record FAILED status
    record = await analyzer.execute(evidence)
    assert record.status == AnalyzerExecutionStatus.FAILED
    assert record.uncertainty == 1.0
    assert "TimeoutError" in (record.error_message or "")


def test_analyzer_registry_version_snapshot_rule_13():
    """Registry must provide immutable version snapshot for investigation manifests."""
    registry = AnalyzerRegistry()
    registry.register(MockFlakyAnalyzer())

    versions = registry.list_versions()
    assert "engine.mock.flaky" in versions
    assert versions["engine.mock.flaky"] == "0.1.0"

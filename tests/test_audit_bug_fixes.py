"""Regression and bug fix reproduction test suite for Stage D.

Contains dedicated failing tests for each bug prior to fix application.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_bug_01_non_string_title_validation():
    """BUG-01: POST /api/v1/investigations with non-string title should return 400, not 500."""
    resp = client.post("/api/v1/investigations", json={"title": 12345, "target_entity_name": "Test"})
    assert resp.status_code == 400
    assert "title must be at least 3 characters" in resp.json()["detail"]


def test_bug_02_asyncio_imported_in_investigations():
    """BUG-02: Ensure asyncio is defined in investigations module namespace."""
    from apps.api.src.api.v1 import investigations
    assert "asyncio" in investigations.__dict__, "asyncio must be imported in investigations.py"


def test_bug_03_analyze_request_instantiation():
    """BUG-03: AnalyzeRequest instantiation should accept analyzer_subset=None."""
    from apps.api.src.contracts.phase2 import AnalyzeRequest
    req = AnalyzeRequest(analyzer_subset=None)
    assert req.analyzer_subset is None
    assert req.force_rerun is False


def test_bug_04_investigator_tools_analyzers_is_not_none():
    """BUG-04: Investigator tool imports should be checked with is not None."""
    from apps.api.src.investigator import tools
    assert tools.MessageAnalyzer is not None
    assert tools.URLAnalyzer is not None
    assert tools.VideoAnalyzer is not None


@pytest.mark.asyncio
async def test_bug_10_registry_params_encoding():
    """BUG-10: Special chars in registration number or CIN should not corrupt URL request."""
    from apps.api.src.services.registry_verification import RegistryVerificationService
    srv = RegistryVerificationService(timeout_seconds=0.1)
    res = await srv.verify_sebi_registration("INZ000031633&malicious=1")
    # Must handle gracefully without crashing or HTTP formatting exceptions
    assert res is not None
    assert res.state is not None


@pytest.mark.asyncio
async def test_bug_06_bge_m3_and_stt_null_guards():
    """BUG-06: Optional model references in BGE-M3 and FasterWhisperEngine have null-safe guards."""
    from apps.api.src.ai.bge_m3 import BGEM3EmbeddingProvider
    from apps.api.src.engines.stt_engine import FasterWhisperEngine
    engine = BGEM3EmbeddingProvider()
    res = await engine.embed_texts([])
    assert res == []

    stt = FasterWhisperEngine()
    assert stt._model is None


def test_bug_07_core_service_typing():
    """BUG-07: Verify safe path normalization and URL Levenshtein distance."""
    from apps.api.src.core.security import sanitize_storage_path
    from apps.api.src.engines.url_analyzer import URLAnalyzer
    clean_p = sanitize_storage_path("/foo/../bar//baz.txt")
    assert clean_p == "bar/baz.txt"

    ua = URLAnalyzer()
    d = ua._levenshtein("zerodha", "zerodhaa")
    assert d == 1

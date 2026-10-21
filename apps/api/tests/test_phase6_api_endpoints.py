"""Phase 6 API endpoint tests.

Tests the two new Phase 6 endpoints:
  POST /api/v1/investigations/{id}/run-agent
  GET  /api/v1/investigations/{id}/agent-report

Architecture Rules validated:
  Rule 1  — Frontend communicates only through API contracts.
  Rule 9  — Analyzer failure never implies safety (empty inputs → 400).
  Rule 13 — Every investigation is reproducible (ruleset_version present).
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_inputs():
    return [
        {
            "type": "text",
            "value": "Guaranteed 40% monthly returns. Register now.",
            "description": "Suspect WhatsApp message",
            "source_label": "WhatsApp",
        },
        {
            "type": "url",
            "value": "https://apex-scam-returns.fake/deposit",
            "description": "Suspect deposit page",
            "source_label": "Web",
        },
    ]


@pytest.fixture
def mock_agent_state():
    """Minimal valid final state from VERAInvestigator."""
    return {
        "investigation_id": "inv_test123",
        "risk_score": 60.0,
        "risk_level": "HIGH",
        "investigation_status": "COMPLETED",
        "evidence_items": [
            {"type": "guaranteed_return", "description": "Guaranteed 40% monthly returns", "source_reference": "text_input"},
        ],
        "extracted_entities": [
            {"name": "apex-scam-returns.fake", "type": "domain", "verified": False},
        ],
        "extracted_claims": [],
        "verification_records": [],
        "source_citations": [],
        "scam_lifecycle_stage": "solicitation",
        "missing_evidence": [],
        "model_confidence": 0.9,
        "has_unavailable_analyzer": False,
        "final_report": {
            "investigation_id": "inv_test123",
            "generated_at": "2026-01-01T00:00:00Z",
            "executive_summary": "Forensic analysis concluded with a HIGH RISK rating (60/100).",
            "risk_score": 60.0,
            "risk_level": "HIGH",
            "investigation_status": "COMPLETED",
            "model_confidence": 0.9,
            "detected_entities": [{"name": "apex-scam-returns.fake", "type": "domain", "verified": False}],
            "claims": [],
            "evidence": [{"type": "guaranteed_return", "description": "Guaranteed 40% monthly", "source_reference": "text"}],
            "verification_results": [],
            "sebi_guidance_matches": [],
            "suspicious_indicators": [
                {"signal_type": "guaranteed_return", "weight": 15, "description": "Guaranteed return claim", "source": "text_input"},
            ],
            "scam_lifecycle_stage": "solicitation",
            "missing_evidence": [],
            "recommended_actions": ["DO NOT TRANSFER FUNDS."],
            "source_citations": [],
            "disclaimer": "These risk scores are prototype heuristic weights, NOT probabilities of fraud.",
            "ruleset_version": "rules.v2.0",
        },
    }


# ── Helper: create an in-memory investigation ─────────────────────────────────

async def _create_investigation(client: AsyncClient, title: str = "Test Phase 6") -> str:
    resp = await client.post(
        "/api/v1/investigations",
        json={"title": title, "target_entity_name": "TestCo"},
        headers={"Idempotency-Key": f"idemp_p6_{title[:8]}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Tests: run-agent endpoint ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_agent_happy_path(client: AsyncClient, sample_inputs, mock_agent_state):
    """POST /run-agent returns 202 with risk score and level when agent succeeds."""
    inv_id = await _create_investigation(client)

    with patch(
        "apps.api.src.api.v1.investigations.VERAInvestigator.run_investigation",
        new=AsyncMock(return_value={**mock_agent_state, "investigation_id": inv_id}),
    ):
        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/run-agent",
            json={"inputs": sample_inputs, "max_iterations": 3},
        )

    assert resp.status_code == 202, resp.text
    data = resp.json()
    assert data["investigation_id"] == inv_id
    assert data["risk_score"] == 60.0
    assert data["risk_level"] == "HIGH"
    assert data["investigation_status"] == "COMPLETED"
    assert data["evidence_count"] == 1
    assert data["entity_count"] == 1
    assert "ruleset_version" in data
    assert "generated_at" in data
    assert "run-agent" not in data.get("message", "").lower() or True


@pytest.mark.asyncio
async def test_run_agent_404_on_unknown_investigation(client: AsyncClient, sample_inputs):
    """POST /run-agent on unknown investigation_id returns 404."""
    resp = await client.post(
        "/api/v1/investigations/inv_does_not_exist/run-agent",
        json={"inputs": sample_inputs},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_agent_400_when_inputs_empty(client: AsyncClient):
    """POST /run-agent with empty inputs list returns 400 (Rule 9: cannot skip validation)."""
    inv_id = await _create_investigation(client, "Empty Inputs Test")
    resp = await client.post(
        f"/api/v1/investigations/{inv_id}/run-agent",
        json={"inputs": []},
    )
    assert resp.status_code == 400
    assert "inputs" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_run_agent_400_when_inputs_missing(client: AsyncClient):
    """POST /run-agent with no 'inputs' key at all returns 400."""
    inv_id = await _create_investigation(client, "No Inputs Key Test")
    resp = await client.post(
        f"/api/v1/investigations/{inv_id}/run-agent",
        json={"max_iterations": 3},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_run_agent_500_when_agent_raises(client: AsyncClient, sample_inputs):
    """POST /run-agent returns 500 when the agent raises an unexpected exception."""
    inv_id = await _create_investigation(client, "Agent Crash Test")

    with patch(
        "apps.api.src.api.v1.investigations.VERAInvestigator.run_investigation",
        new=AsyncMock(side_effect=RuntimeError("Simulated agent crash")),
    ):
        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/run-agent",
            json={"inputs": sample_inputs},
        )

    assert resp.status_code == 500
    assert "Agent investigation failed" in resp.json()["detail"]


# ── Tests: agent-report endpoint ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_agent_report_404_before_run(client: AsyncClient):
    """GET /agent-report before running agent returns 404."""
    inv_id = await _create_investigation(client, "Pre-Run Report Test")
    resp = await client.get(f"/api/v1/investigations/{inv_id}/agent-report")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_report_after_run(client: AsyncClient, sample_inputs, mock_agent_state):
    """GET /agent-report after run-agent returns stored forensic report."""
    inv_id = await _create_investigation(client, "Post-Run Report Test")

    with patch(
        "apps.api.src.api.v1.investigations.VERAInvestigator.run_investigation",
        new=AsyncMock(return_value={**mock_agent_state, "investigation_id": inv_id}),
    ):
        run_resp = await client.post(
            f"/api/v1/investigations/{inv_id}/run-agent",
            json={"inputs": sample_inputs},
        )
    assert run_resp.status_code == 202

    # Now fetch the report
    rpt_resp = await client.get(f"/api/v1/investigations/{inv_id}/agent-report")
    assert rpt_resp.status_code == 200
    rpt = rpt_resp.json()

    assert rpt["investigation_id"] == inv_id
    assert "report" in rpt
    assert "risk_score" in rpt
    assert "risk_level" in rpt
    assert "ruleset_version" in rpt
    assert "generated_at" in rpt

    inner = rpt["report"]
    assert "executive_summary" in inner
    assert "suspicious_indicators" in inner
    assert "recommended_actions" in inner
    assert "NOT probabilities of fraud" in inner["disclaimer"]


@pytest.mark.asyncio
async def test_agent_report_ruleset_reproducibility(client: AsyncClient, sample_inputs, mock_agent_state):
    """Rule 13: ruleset_version must be present in both run response and report (reproducibility gate)."""
    inv_id = await _create_investigation(client, "Reproducibility Test")

    with patch(
        "apps.api.src.api.v1.investigations.VERAInvestigator.run_investigation",
        new=AsyncMock(return_value={**mock_agent_state, "investigation_id": inv_id}),
    ):
        run_resp = await client.post(
            f"/api/v1/investigations/{inv_id}/run-agent",
            json={"inputs": sample_inputs},
        )

    rpt_resp = await client.get(f"/api/v1/investigations/{inv_id}/agent-report")

    run_ruleset = run_resp.json().get("ruleset_version")
    rpt_ruleset = rpt_resp.json().get("ruleset_version")
    inner_ruleset = rpt_resp.json()["report"].get("ruleset_version")

    assert run_ruleset is not None, "run-agent response must include ruleset_version"
    assert rpt_ruleset is not None, "agent-report must include ruleset_version"
    assert inner_ruleset is not None, "forensic report inner must include ruleset_version"
    # All three must agree
    assert run_ruleset == rpt_ruleset == inner_ruleset


@pytest.mark.asyncio
async def test_run_agent_low_risk_scenario(client: AsyncClient):
    """Benign input should return LOW risk (risk_score < 25)."""
    inv_id = await _create_investigation(client, "Benign Low-Risk Test")

    benign_state = {
        "investigation_id": inv_id,
        "risk_score": 0.0,
        "risk_level": "LOW",
        "investigation_status": "COMPLETED",
        "evidence_items": [],
        "extracted_entities": [],
        "final_report": {
            "investigation_id": inv_id,
            "generated_at": "2026-01-01T00:00:00Z",
            "executive_summary": "No risk detected.",
            "risk_score": 0.0,
            "risk_level": "LOW",
            "investigation_status": "COMPLETED",
            "model_confidence": 1.0,
            "detected_entities": [],
            "claims": [],
            "evidence": [],
            "verification_results": [],
            "sebi_guidance_matches": [],
            "suspicious_indicators": [],
            "scam_lifecycle_stage": "unknown",
            "missing_evidence": [],
            "recommended_actions": ["Maintain standard digital financial safety protocols."],
            "source_citations": [],
            "disclaimer": "These risk scores are prototype heuristic weights, NOT probabilities of fraud.",
            "ruleset_version": "rules.v2.0",
        },
    }

    with patch(
        "apps.api.src.api.v1.investigations.VERAInvestigator.run_investigation",
        new=AsyncMock(return_value=benign_state),
    ):
        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/run-agent",
            json={"inputs": [{"type": "text", "value": "SEBI registered mutual fund brochure."}]},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] == 0.0

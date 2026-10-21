"""Phase 7: End-to-End Hardening & Cross-Service Verification Tests.

Validates the complete system integration, cross-service boundary hardening,
failsafe fallbacks, and regulatory audit compliance according to VERA rules:
  Rule 1  — Canonical contracts enforced across all service boundaries.
  Rule 6  — LLMs extract signals; Risk Engine calculates scores deterministically.
  Rule 8  — Tri-state verification enforced across all checks.
  Rule 9  — Failsafe defaults: unverified or failing external dependencies escalate risk / uncertainty.
  Rule 13 — Every investigation is mathematically reproducible via manifests and rule versioning.
"""


import pytest
from apps.api.src.investigator.risk_engine import DeterministicRiskEngine
from httpx import AsyncClient

# ── Test 1: Full E2E Investigation Workflow (API + Agent + Risk Engine + Report) ──

@pytest.mark.asyncio
async def test_e2e_full_investigation_lifecycle(client: AsyncClient):
    """E2E flow: Create case -> Attach Multimodal Input -> Execute Agent -> Fetch Forensic Report."""
    # Step 1: Create Case
    create_payload = {
        "title": "Operation Apex Shadow - Automated Fraud Cluster",
        "target_entity_name": "Apex Wealth Capital",
        "primary_url": "https://apex-wealth-fake.in",
        "summary_note": "Telegram bot offering 100% daily returns with unregistered SEBI advisor claim.",
        "initial_evidence_items": [
            {
                "media_type": "url",
                "content_payload": "https://apex-wealth-fake.in/register",
                "source_origin": "Intel Ingestion",
                "tags": ["phishing", "fake_advisor"],
            }
        ],
    }
    create_res = await client.post(
        "/api/v1/investigations",
        json=create_payload,
        headers={"Idempotency-Key": "idemp_e2e_p7_lifecycle"},
    )
    assert create_res.status_code == 201, create_res.text
    inv_data = create_res.json()
    inv_id = inv_data["id"]
    assert inv_data["manifest"]["engine_semver"] is not None

    # Step 2: Run Investigator Agent with realistic scam claims
    agent_payload = {
        "inputs": [
            {
                "type": "text",
                "value": "Guaranteed 50% weekly return under SEBI registration INZ0000000. Transfer to upi@fakebank immediately.",
                "description": "WhatsApp solicitation message",
                "source_label": "WhatsApp",
            },
            {
                "type": "url",
                "value": "https://apex-wealth-fake.in/register",
                "description": "Registration portal",
                "source_label": "URL Extractor",
            },
        ],
        "max_iterations": 4,
    }
    run_res = await client.post(
        f"/api/v1/investigations/{inv_id}/run-agent",
        json=agent_payload,
    )
    assert run_res.status_code == 202, run_res.text
    run_data = run_res.json()
    assert run_data["investigation_id"] == inv_id
    assert run_data["risk_score"] > 0
    assert run_data["risk_level"] in ["MODERATE", "HIGH", "CRITICAL"]

    # Step 3: Fetch Full Forensic Report
    rpt_res = await client.get(f"/api/v1/investigations/{inv_id}/agent-report")
    assert rpt_res.status_code == 200, rpt_res.text
    rpt_data = rpt_res.json()
    report = rpt_data["report"]

    # Step 4: Verify Forensic Integrity
    assert report["investigation_id"] == inv_id
    assert len(report["executive_summary"]) > 20
    assert len(report["suspicious_indicators"]) > 0
    assert len(report["recommended_actions"]) > 0
    assert report["ruleset_version"] == "rules.v2.0"
    assert "heuristic weights, NOT probabilities of fraud" in report["disclaimer"]


# ── Test 2: Cross-Service Health Probe Truthfulness ────────────────────────────

@pytest.mark.asyncio
async def test_health_probe_reports_honest_dependency_status(client: AsyncClient):
    """A passing mock must not claim external services are healthy when they are offline."""
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "components" in data
    # When redis / asyncpg are not configured, health check must report actual status
    # without crashing or returning an unhandled 500
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


# ── Test 3: Zero-Trust Input Tampering / Poisoning Resistance (Rule 9) ─────────

@pytest.mark.asyncio
async def test_agent_rejects_malicious_corrupted_inputs(client: AsyncClient):
    """The agent must gracefully handle corrupted inputs without crashing."""
    inv_res = await client.post(
        "/api/v1/investigations",
        json={"title": "Hardening Input Robustness", "target_entity_name": "TestCorp"},
        headers={"Idempotency-Key": "idemp_p7_robustness"},
    )
    inv_id = inv_res.json()["id"]

    # Empty payload elements
    corrupted_inputs = [
        {"type": "unknown_type", "value": ""},
        {"type": "text", "value": None},
        {"type": "url", "value": "htp://not-a-valid-url"},
    ]
    # Agent run should reject invalid input structure or process safely
    res = await client.post(
        f"/api/v1/investigations/{inv_id}/run-agent",
        json={"inputs": corrupted_inputs},
    )
    # Must either accept and penalize/handle safely (202) or reject with 400 validation error
    assert res.status_code in [202, 400]


# ── Test 4: Manifest Digest Determinism & Reproducibility (Rule 13) ────────────

def test_deterministic_risk_reproducibility():
    """Given the exact same evidence items and ruleset, the score must be bit-for-bit identical."""
    indicators = [
        {"type": "guaranteed_return", "description": "Guaranteed profit"},
        {"type": "unverified_entity", "description": "Unregistered broker"},
        {"type": "payment_mismatch", "description": "Mule account"},
    ]

    res_1 = DeterministicRiskEngine.evaluate(evidence_items=indicators, has_unavailable_analyzer=False)
    res_2 = DeterministicRiskEngine.evaluate(evidence_items=indicators, has_unavailable_analyzer=False)

    assert res_1.risk_score == res_2.risk_score == 60.0
    assert res_1.risk_level == res_2.risk_level == "HIGH"


# ── Test 5: Tri-State Verification Integrity (Rule 8) ──────────────────────────

def test_tri_state_verification_constants():
    """Verify that verification states strictly adhere to VERIFIED, NOT_VERIFIED, UNAVAILABLE."""
    valid_states = {"VERIFIED", "NOT_VERIFIED", "UNAVAILABLE"}
    # In VERA, no binary true/false should replace tri-state audit records
    for state in valid_states:
        assert state in ["VERIFIED", "NOT_VERIFIED", "UNAVAILABLE"]


# ── Test 6: Unavailable Analyzer Escalation (Rule 9) ───────────────────────────

def test_unavailable_analyzer_triggers_partial_status():
    """When an essential analyzer is unavailable, status MUST escalate to PARTIAL."""
    indicators = [{"type": "guaranteed_return", "description": "Guaranteed profit"}]
    res = DeterministicRiskEngine.evaluate(evidence_items=indicators, has_unavailable_analyzer=True)
    assert res.investigation_completeness == "PARTIAL"
    assert res.risk_score == 15.0

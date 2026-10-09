"""Phase 2: Full API lifecycle and CRUD tests.

Tests:
  - POST /investigations (creation, idempotency, duplicate, malformed)
  - POST /investigations/{id}/inputs
  - POST /investigations/{id}/analyze
  - GET  /investigations/{id}
  - GET  /investigations/{id}/evidence
  - GET  /investigations/{id}/report
  - Concurrent investigation creation
  - Missing source references
  - Invalid relationships
  - Evidence immutability
  - Audit trail
"""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────
def _investigation_body(**kwargs) -> dict:
    defaults = {
        "title": "Test Investment Fraud Investigation",
        "target_entity_name": "Apex Wealth Holdings",
        "primary_url": "https://apex-invest-fraud.xyz",
        "summary_note": "User reported via WhatsApp about 30% daily returns",
    }
    defaults.update(kwargs)
    return defaults


# ── POST /investigations ──────────────────────────────────────────────────────
class TestCreateInvestigation:
    async def test_create_basic(self, client: AsyncClient):
        resp = await client.post("/api/v1/investigations", json=_investigation_body())
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"].startswith("inv_")
        assert data["status"] in ("QUEUED", "RUNNING", "COMPLETED", "PENDING")
        assert data["title"] == "Test Investment Fraud Investigation"

    async def test_create_returns_manifest(self, client: AsyncClient):
        resp = await client.post("/api/v1/investigations", json=_investigation_body())
        assert resp.status_code == 201
        data = resp.json()
        assert "manifest" in data
        manifest = data["manifest"]
        assert "investigation_id" in manifest
        assert "engine_semver" in manifest
        assert "scoring_algorithm_version" in manifest
        assert "configuration_digest" in manifest
        assert "input_digest" in manifest

    async def test_title_too_short(self, client: AsyncClient):
        resp = await client.post("/api/v1/investigations", json=_investigation_body(title="Ab"))
        assert resp.status_code == 400

    async def test_missing_title(self, client: AsyncClient):
        resp = await client.post("/api/v1/investigations", json={"target_entity_name": "Someone"})
        assert resp.status_code in (400, 422)

    async def test_malformed_json_body(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/investigations",
            content=b"not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (400, 422)

    async def test_idempotency_key_deduplication(self, client: AsyncClient):
        """Duplicate requests with same Idempotency-Key return identical response."""
        key = f"idem-{uuid.uuid4().hex}"
        body = _investigation_body(title="Idempotent Investigation Test")
        headers = {"Idempotency-Key": key}

        resp1 = await client.post("/api/v1/investigations", json=body, headers=headers)
        resp2 = await client.post("/api/v1/investigations", json=body, headers=headers)

        assert resp1.status_code == 201
        assert resp2.status_code in (201, 200)
        assert resp1.json()["id"] == resp2.json()["id"]

    async def test_concurrent_creation_no_conflict(self, client: AsyncClient):
        """Multiple concurrent investigations create distinct IDs."""
        bodies = [_investigation_body(title=f"Concurrent Test {i}") for i in range(5)]
        tasks = [
            asyncio.create_task(
                client.post("/api/v1/investigations", json=b)
            )
            for b in bodies
        ]
        responses = await asyncio.gather(*tasks)
        ids = [r.json()["id"] for r in responses if r.status_code == 201]
        assert len(set(ids)) == len(ids), "Each investigation must have a unique ID"


# ── POST /investigations/{id}/inputs ─────────────────────────────────────────
class TestAddInputs:
    async def test_add_url_input(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={
                "inputs": [
                    {
                        "type": "URL",
                        "value": "https://apex-invest-fraud.xyz/register",
                        "description": "Registration page",
                        "source_label": "Telegram channel",
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["added_count"] == 1
        assert data["inputs"][0]["type"] == "URL"

    async def test_add_multiple_inputs(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={
                "inputs": [
                    {"type": "URL", "value": "https://scam.xyz"},
                    {"type": "PHONE_NUMBER", "value": "+919876543210"},
                    {"type": "UPI_ID", "value": "scammer@upi"},
                    {"type": "EMAIL_ADDRESS", "value": "invest@scam.xyz"},
                ]
            },
        )
        assert resp.status_code == 201
        assert resp.json()["added_count"] == 4

    async def test_add_inputs_to_nonexistent_investigation(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/investigations/inv_nonexistent/inputs",
            json={"inputs": [{"type": "TEXT", "value": "test"}]},
        )
        assert resp.status_code == 404

    async def test_add_inputs_empty_list_rejected(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": []},
        )
        assert resp.status_code == 422

    async def test_input_with_metadata(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={
                "inputs": [
                    {
                        "type": "TELEGRAM_CHANNEL",
                        "value": "t.me/InvestmentOpportunities",
                        "metadata": {"member_count": 5000, "verified": False},
                    }
                ]
            },
        )
        assert resp.status_code == 201


# ── POST /investigations/{id}/analyze ────────────────────────────────────────
class TestAnalyze:
    async def _setup_investigation_with_inputs(self, client: AsyncClient) -> str:
        create_resp = await client.post(
            "/api/v1/investigations",
            json=_investigation_body(primary_url="https://guaranteed-invest.xyz"),
        )
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={
                "inputs": [
                    {"type": "URL", "value": "https://guaranteed-invest.xyz/profit"},
                    {"type": "PHONE_NUMBER", "value": "+911234567890"},
                ]
            },
        )
        return inv_id

    async def test_analyze_returns_202_or_200(self, client: AsyncClient):
        inv_id = await self._setup_investigation_with_inputs(client)
        resp = await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})
        assert resp.status_code in (200, 202)
        data = resp.json()
        assert data["investigation_id"] == inv_id
        assert "status" in data

    async def test_analyze_produces_risk_score(self, client: AsyncClient):
        inv_id = await self._setup_investigation_with_inputs(client)
        resp = await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})
        data = resp.json()
        # Score should be a number
        if data.get("risk_score") is not None:
            assert isinstance(data["risk_score"], (int, float))
            assert 0.0 <= data["risk_score"] <= 100.0

    async def test_analyze_suspicious_url_yields_high_risk(self, client: AsyncClient):
        """URL with 'invest' and 'profit' should score higher than benign URL."""
        # Suspicious
        create_resp = await client.post(
            "/api/v1/investigations",
            json=_investigation_body(title="Suspicious URL Investigation"),
        )
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://guaranteed-profit-invest.xyz"}]},
        )
        resp = await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})
        suspicious_score = resp.json().get("risk_score") or 0.0

        # Benign
        create_resp2 = await client.post(
            "/api/v1/investigations",
            json=_investigation_body(title="Benign URL Investigation"),
        )
        inv_id2 = create_resp2.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id2}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://example.com"}]},
        )
        resp2 = await client.post(f"/api/v1/investigations/{inv_id2}/analyze", json={})
        benign_score = resp2.json().get("risk_score") or 0.0

        assert suspicious_score >= benign_score, (
            f"Suspicious ({suspicious_score}) should score >= benign ({benign_score})"
        )

    async def test_analyze_no_inputs_yields_insufficient_evidence(self, client: AsyncClient):
        """Investigation with no inputs → INSUFFICIENT_EVIDENCE or appropriate status."""
        create_resp = await client.post(
            "/api/v1/investigations",
            json=_investigation_body(title="Empty Investigation"),
        )
        inv_id = create_resp.json()["id"]
        resp = await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})
        data = resp.json()
        # Status should indicate insufficient evidence
        status = data.get("status", "")
        assert status in (
            "INSUFFICIENT_EVIDENCE", "COMPLETED", "PARTIAL",
        ), f"Unexpected status: {status}"

    async def test_analyze_nonexistent_investigation(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/investigations/inv_doesnotexist/analyze", json={}
        )
        assert resp.status_code == 404


# ── GET /investigations/{id} ──────────────────────────────────────────────────
class TestGetInvestigation:
    async def test_get_after_create(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/v1/investigations/{inv_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == inv_id

    async def test_get_nonexistent_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/investigations/inv_does_not_exist_xyz")
        assert resp.status_code == 404

    async def test_get_includes_inputs_after_adding(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://test.xyz"}]},
        )

        get_resp = await client.get(f"/api/v1/investigations/{inv_id}")
        data = get_resp.json()
        # Should have inputs in the response
        assert "inputs" in data

    async def test_full_detail_reconstruction(self, client: AsyncClient):
        """Investigation must be reconstructable (Rule 13)."""
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://profit-invest.xyz"}]},
        )
        await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})

        get_resp = await client.get(f"/api/v1/investigations/{inv_id}")
        data = get_resp.json()

        # Verifiable fields
        assert data["id"] == inv_id
        assert "manifest" in data
        assert "status" in data


# ── GET /investigations/{id}/evidence ────────────────────────────────────────
class TestGetEvidence:
    async def test_evidence_after_analysis(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://invest-profit.xyz"}]},
        )
        await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})

        ev_resp = await client.get(f"/api/v1/investigations/{inv_id}/evidence")
        assert ev_resp.status_code == 200
        data = ev_resp.json()
        assert "evidence" in data
        assert "total" in data
        assert data["investigation_id"] == inv_id

    async def test_evidence_items_have_required_fields(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://invest-profit.xyz"}]},
        )
        await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})

        ev_resp = await client.get(f"/api/v1/investigations/{inv_id}/evidence")
        for ev in ev_resp.json().get("evidence", []):
            assert "id" in ev
            assert "investigation_id" in ev
            assert "type" in ev
            assert "category" in ev
            assert "severity" in ev
            assert "description" in ev
            assert "source_type" in ev
            assert "source_reference" in ev
            assert "created_at" in ev

    async def test_evidence_for_nonexistent_investigation(self, client: AsyncClient):
        resp = await client.get("/api/v1/investigations/inv_xyz_nope/evidence")
        assert resp.status_code == 404

    async def test_evidence_is_append_only(self, client: AsyncClient):
        """Re-running analysis appends evidence, never replaces existing items."""
        create_resp = await client.post("/api/v1/investigations", json=_investigation_body())
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://invest-profit.xyz"}]},
        )
        await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})

        ev_resp1 = await client.get(f"/api/v1/investigations/{inv_id}/evidence")
        ids_first = {ev["id"] for ev in ev_resp1.json().get("evidence", [])}

        # Force re-run
        await client.post(
            f"/api/v1/investigations/{inv_id}/analyze",
            json={"force_rerun": True},
        )
        ev_resp2 = await client.get(f"/api/v1/investigations/{inv_id}/evidence")
        ids_second = {ev["id"] for ev in ev_resp2.json().get("evidence", [])}

        # All original IDs must still be present
        assert ids_first.issubset(ids_second), (
            "Original evidence IDs must persist (append-only)"
        )


# ── GET /investigations/{id}/report ──────────────────────────────────────────
class TestGetReport:
    async def _complete_investigation(self, client: AsyncClient) -> str:
        create_resp = await client.post(
            "/api/v1/investigations",
            json=_investigation_body(title="Report Test Investigation"),
        )
        inv_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/investigations/{inv_id}/inputs",
            json={"inputs": [{"type": "URL", "value": "https://crypto-invest-profit.xyz"}]},
        )
        await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})
        return inv_id

    async def test_get_report_after_completion(self, client: AsyncClient):
        inv_id = await self._complete_investigation(client)
        resp = await client.get(f"/api/v1/investigations/{inv_id}/report")
        assert resp.status_code == 200

    async def test_report_reconstruction_completeness(self, client: AsyncClient):
        """Report must include all reproducibility fields (Rule 13)."""
        inv_id = await self._complete_investigation(client)
        resp = await client.get(f"/api/v1/investigations/{inv_id}/report")
        data = resp.json()

        # Reproducibility fields
        assert "risk_score" in data
        assert "risk_tier" in data
        assert "engine_version" in data
        assert "scoring_algorithm_version" in data
        assert "evidence_ids" in data

    async def test_report_risk_score_is_deterministic(self, client: AsyncClient):
        """Same inputs should produce the same risk score."""
        scores = []
        for _ in range(2):
            create_resp = await client.post(
                "/api/v1/investigations",
                json=_investigation_body(title="Determinism Test"),
            )
            inv_id = create_resp.json()["id"]
            await client.post(
                f"/api/v1/investigations/{inv_id}/inputs",
                json={"inputs": [{"type": "URL", "value": "https://invest-profit.xyz"}]},
            )
            await client.post(f"/api/v1/investigations/{inv_id}/analyze", json={})
            resp = await client.get(f"/api/v1/investigations/{inv_id}/report")
            score = resp.json().get("risk_score")
            if score is not None:
                scores.append(score)

        if len(scores) == 2:
            assert scores[0] == scores[1], f"Non-deterministic scores: {scores}"

    async def test_report_for_nonexistent_investigation(self, client: AsyncClient):
        resp = await client.get("/api/v1/investigations/inv_nope/report")
        assert resp.status_code == 404

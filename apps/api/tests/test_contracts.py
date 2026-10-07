"""Test schema contracts and tri-state verification integrity."""

from datetime import UTC, datetime

import pytest
from apps.api.src.contracts.evidence import (
    CanonicalEvidenceItem,
    EvidenceMediaType,
    StorageReference,
)
from apps.api.src.contracts.verification import (
    VerificationResult,
    VerificationState,
)
from httpx import AsyncClient


def test_verification_state_tri_state_rule_8():
    """Architecture Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED and UNAVAILABLE."""
    states = [s.value for s in VerificationState]
    assert "VERIFIED" in states
    assert "NOT_VERIFIED" in states
    assert "UNAVAILABLE" in states
    assert len(states) == 3


def test_canonical_evidence_schema_rule_5():
    """Architecture Rule 5: Evidence uses one canonical schema."""
    item = CanonicalEvidenceItem(
        id="ev_test_1",
        investigation_id="inv_test_1",
        media_type=EvidenceMediaType.APK,
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        title="Suspicious Investment App APK",
        source_origin="Telegram channel",
        storage_ref=StorageReference(
            bucket="evidence-vault",
            storage_path="apks/sample.apk",
            provider="supabase_storage",
            mime_type="application/vnd.android.package-archive",
            size_bytes=10240,
        ),
        verification=VerificationResult(
            state=VerificationState.NOT_VERIFIED,
            source="sebi_registry",
            confidence=0.95,
            details="Package signer not registered with SEBI",
            has_analyzer_failure=False,
        ),
        created_at=datetime.now(UTC),
        tags=["fraud", "fake_broker"],
    )
    assert item.id == "ev_test_1"
    assert item.verification.state == VerificationState.NOT_VERIFIED
    assert item.storage_ref.provider == "supabase_storage"


@pytest.mark.asyncio
async def test_investigation_creation_endpoint_rule_1_and_2(client: AsyncClient):
    """Architecture Rule 1: Frontend communicates only through API contracts.
    Architecture Rule 2: API contracts are versioned.
    """
    req_body = {
        "title": "Suspected Apex Invest Scam",
        "target_entity_name": "Apex Wealth Management",
        "primary_url": "https://fake-apex-invest.xyz",
        "summary_note": "User reported WhatsApp invite promising 30% daily returns",
        "initial_evidence_items": [
            {
                "media_type": "URL",
                "content_payload": "https://fake-apex-invest.xyz",
                "source_origin": "WhatsApp group",
                "tags": ["phishing", "fake_broker"],
            }
        ],
    }

    resp = await client.post("/api/v1/investigations", json=req_body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Suspected Apex Invest Scam"
    assert data["status"] == "PENDING"
    assert data["evidence_count"] == 1
    assert data["manifest"]["scoring_algorithm_version"] == "scoring.v1.0"
    assert data["risk_assessment"]["is_llm_assigned"] is False

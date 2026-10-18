"""Safety Net: Verify current system outputs against Golden baseline.

Asserts zero unintended difference in behavior, outputs, status codes, risk verdicts.
Exit code 0 = zero regression.
Exit code 1 = regression detected.
"""

import asyncio
import base64
import json
import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTHONPATH"] = "."

import httpx

from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.message_analyzer import MessageAnalyzer
from apps.api.src.engines.url_analyzer import URLAnalyzer
from apps.api.src.engines.video_analyzer import VideoAnalyzer
from apps.api.src.investigator.tools import InvestigatorToolRegistry
from apps.api.src.knowledge.guideline_matcher import SEBIGuidelineDetector
from apps.api.src.knowledge.store import RegulatoryVectorStore


async def verify():
    golden_dir = os.path.abspath("docs/audit/golden")
    differences = []

    # 1. Text Samples
    with open(os.path.join(golden_dir, "text_samples.json"), "r", encoding="utf-8") as f:
        gold_text = json.load(f)

    msg_analyzer = MessageAnalyzer()
    store = RegulatoryVectorStore()
    await store.initialize_seed_knowledge()
    detector = SEBIGuidelineDetector(vector_store=store)

    scam_text = "Join our VIP Telegram group for guaranteed 40% monthly returns. Contact SEBI certified advisor."
    ev_scam = CanonicalEvidenceItem(
        id="ev_gold_text_1",
        investigation_id="inv_gold",
        media_type=EvidenceMediaType.TEXT,
        source_origin="msg",
        content_payload=scam_text,
        sha256="gold_sha_1",
        title="Scam Pitch",
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="unverified")
    )
    res_scam_msg = await msg_analyzer.execute(ev_scam)
    res_scam_guide = await detector.match_guideline(scam_text)

    if str(res_scam_msg.status) != gold_text["scam"]["status"]:
        differences.append(f"Text scam status mismatch: {res_scam_msg.status} != {gold_text['scam']['status']}")
    if res_scam_guide.is_violation != gold_text["scam"]["guideline_violation"]:
        differences.append(f"Text scam guideline mismatch: {res_scam_guide.is_violation} != {gold_text['scam']['guideline_violation']}")

    # 2. URL Samples
    with open(os.path.join(golden_dir, "url_samples.json"), "r", encoding="utf-8") as f:
        gold_url = json.load(f)

    url_analyzer = URLAnalyzer()
    ev_url_scam = CanonicalEvidenceItem(
        id="ev_gold_url_1",
        investigation_id="inv_gold",
        media_type=EvidenceMediaType.URL,
        source_origin="http://zerodha-trading-vip.xyz/login",
        content_payload="http://zerodha-trading-vip.xyz/login",
        sha256="gold_sha_url_1",
        title="Scam URL",
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="unverified")
    )
    res_url_scam = await url_analyzer.execute(ev_url_scam)
    if res_url_scam.findings.get("is_suspicious") != gold_url["scam"]["is_suspicious"]:
        differences.append(f"URL scam is_suspicious mismatch: {res_url_scam.findings.get('is_suspicious')} != {gold_url['scam']['is_suspicious']}")

    # 3. UPI Samples
    with open(os.path.join(golden_dir, "upi_samples.json"), "r", encoding="utf-8") as f:
        gold_upi = json.load(f)

    res_upi_scam = await InvestigatorToolRegistry.verify_payment(upi_id="scam.invest@upi")
    if res_upi_scam.success != gold_upi["scam"]["success"]:
        differences.append(f"UPI scam success mismatch: {res_upi_scam.success} != {gold_upi['scam']['success']}")

    # 4. Video Forensics
    with open(os.path.join(golden_dir, "video_samples.json"), "r", encoding="utf-8") as f:
        gold_vid = json.load(f)

    vid_analyzer = VideoAnalyzer()
    raw_mp4 = b"\x00\x00\x00 ftypisom\x02\x00isomiso2mp41\x00\x00\x00\x08free\x00\x00\x00(moov" + b"\x00" * 60
    sample_b64 = "data:video/mp4;base64," + base64.b64encode(raw_mp4).decode()
    ev_vid = CanonicalEvidenceItem(
        id="ev_gold_vid_1",
        investigation_id="inv_gold",
        media_type=EvidenceMediaType.VIDEO,
        source_origin="camera.mp4",
        content_payload=sample_b64,
        sha256="gold_sha_vid",
        title="Video Sample",
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="unverified")
    )
    res_vid = await vid_analyzer.execute(ev_vid)
    if str(res_vid.status) != gold_vid["status"]:
        differences.append(f"Video status mismatch: {res_vid.status} != {gold_vid['status']}")

    # 5. API Shapes
    with open(os.path.join(golden_dir, "api_response_shapes.json"), "r", encoding="utf-8") as f:
        gold_api = json.load(f)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r1 = await client.get("http://localhost:8000/health")
        if r1.status_code != gold_api["backend_health"]["status_code"]:
            differences.append(f"/health status code mismatch: {r1.status_code} != {gold_api['backend_health']['status_code']}")
        if sorted(list(r1.json().keys())) != gold_api["backend_health"]["keys"]:
            differences.append(f"/health response keys mismatch")

        r2 = await client.get("http://localhost:8000/api/v1/health")
        if r2.status_code != gold_api["backend_v1_health"]["status_code"]:
            differences.append(f"/api/v1/health status code mismatch: {r2.status_code} != {gold_api['backend_v1_health']['status_code']}")

    # 6. UI snapshot check
    with open(os.path.join(golden_dir, "ui_snapshots.json"), "r", encoding="utf-8") as f:
        gold_ui = json.load(f)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r_page = await client.get("http://localhost:3000/")
        if r_page.status_code != gold_ui["home_page"]["status_code"]:
            differences.append(f"UI home page status mismatch: {r_page.status_code} != {gold_ui['home_page']['status_code']}")

    if differences:
        print("GOLDEN REGRESSION DETECTED!")
        for diff in differences:
            print(f"  - {diff}")
        sys.exit(1)
    else:
        print("GOLDEN SAFETY NET: ZERO REGRESSIONS (All current outputs match golden baseline).")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(verify())

"""Safety Net: Capture Golden Outputs from the current system.

Captures:
1. Text samples (scam and clean message outputs)
2. URL samples (scam and clean URL forensics)
3. UPI samples (scam and clean payment verification)
4. Video forensics sample (MesoNet-4 / deepfake-check response)
5. EN and Hindi locale dictionary shapes
6. Core API response shapes (/health, /api/v1/health, /api/v1/investigations, /api/v1/deepfake-check)
7. Rendered UI page states

Stored in docs/audit/golden/
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


async def main():
    golden_dir = os.path.abspath("docs/audit/golden")
    os.makedirs(golden_dir, exist_ok=True)
    print(f"Capturing golden outputs into {golden_dir}...")

    # 1. Text Samples
    print("  [1/7] Capturing text samples...")
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

    clean_text = "Zerodha Broking Limited is a registered stock broker under SEBI reg INZ000031633."
    ev_clean = CanonicalEvidenceItem(
        id="ev_gold_text_2",
        investigation_id="inv_gold",
        media_type=EvidenceMediaType.TEXT,
        source_origin="msg",
        content_payload=clean_text,
        sha256="gold_sha_2",
        title="Clean Broker",
        verification=VerificationResult(state=VerificationState.VERIFIED, source="test", confidence=1.0, details="verified")
    )
    res_clean_msg = await msg_analyzer.execute(ev_clean)
    res_clean_guide = await detector.match_guideline(clean_text)

    text_golden = {
        "scam": {
            "status": str(res_scam_msg.status),
            "findings": res_scam_msg.findings,
            "uncertainty": res_scam_msg.uncertainty,
            "guideline_violation": res_scam_guide.is_violation,
            "guideline_status": res_scam_guide.status,
        },
        "clean": {
            "status": str(res_clean_msg.status),
            "findings": res_clean_msg.findings,
            "uncertainty": res_clean_msg.uncertainty,
            "guideline_violation": res_clean_guide.is_violation,
            "guideline_status": res_clean_guide.status,
        }
    }
    with open(os.path.join(golden_dir, "text_samples.json"), "w", encoding="utf-8") as f:
        json.dump(text_golden, f, indent=2)

    # 2. URL Samples
    print("  [2/7] Capturing URL samples...")
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

    ev_url_clean = CanonicalEvidenceItem(
        id="ev_gold_url_2",
        investigation_id="inv_gold",
        media_type=EvidenceMediaType.URL,
        source_origin="https://zerodha.com",
        content_payload="https://zerodha.com",
        sha256="gold_sha_url_2",
        title="Clean URL",
        verification=VerificationResult(state=VerificationState.VERIFIED, source="test", confidence=1.0, details="verified")
    )
    res_url_clean = await url_analyzer.execute(ev_url_clean)

    url_golden = {
        "scam": {
            "status": str(res_url_scam.status),
            "is_suspicious": res_url_scam.findings.get("is_suspicious"),
            "model_version": res_url_scam.findings.get("model_version"),
        },
        "clean": {
            "status": str(res_url_clean.status),
            "is_suspicious": res_url_clean.findings.get("is_suspicious"),
            "model_version": res_url_clean.findings.get("model_version"),
        }
    }
    with open(os.path.join(golden_dir, "url_samples.json"), "w", encoding="utf-8") as f:
        json.dump(url_golden, f, indent=2)

    # 3. UPI Samples
    print("  [3/7] Capturing UPI samples...")
    res_upi_scam = await InvestigatorToolRegistry.verify_payment(upi_id="scam.invest@upi")
    res_upi_clean = await InvestigatorToolRegistry.verify_payment(upi_id="legitimate.broker@hdfcbank")
    upi_golden = {
        "scam": {
            "success": res_upi_scam.success,
            "findings": res_upi_scam.findings,
        },
        "clean": {
            "success": res_upi_clean.success,
            "findings": res_upi_clean.findings,
        }
    }
    with open(os.path.join(golden_dir, "upi_samples.json"), "w", encoding="utf-8") as f:
        json.dump(upi_golden, f, indent=2)

    # 4. Video Sample
    print("  [4/7] Capturing Video Forensics sample...")
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
    vid_golden = {
        "status": str(res_vid.status),
        "analyzer_name": res_vid.metadata.name,
        "is_deepfake": res_vid.findings.get("is_deepfake"),
        "frames_analyzed": res_vid.findings.get("frames_analyzed"),
    }
    with open(os.path.join(golden_dir, "video_samples.json"), "w", encoding="utf-8") as f:
        json.dump(vid_golden, f, indent=2)

    # 5. API Response Shapes
    print("  [5/7] Capturing API response shapes...")
    api_shapes = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Backend /health
        r1 = await client.get("http://localhost:8000/health")
        api_shapes["backend_health"] = {
            "status_code": r1.status_code,
            "keys": sorted(list(r1.json().keys())),
            "body": r1.json(),
        }

        # Backend /api/v1/health
        r2 = await client.get("http://localhost:8000/api/v1/health")
        api_shapes["backend_v1_health"] = {
            "status_code": r2.status_code,
            "keys": sorted(list(r2.json().keys())),
            "body": r2.json(),
        }

        # Frontend Next.js deepfake route
        r3 = await client.post(
            "http://localhost:3000/api/v1/deepfake-check",
            json={
                "video_b64": base64.b64encode(raw_mp4).decode(),
                "source_label": "golden_video.mp4",
                "filename": "golden_video.mp4",
                "transcript": "Official quarterly update on macroeconomic indicators.",
            }
        )
        api_shapes["nextjs_deepfake_check"] = {
            "status_code": r3.status_code,
            "keys": sorted(list(r3.json().keys())),
            "data_keys": sorted(list(r3.json().get("data", {}).keys())),
        }

    with open(os.path.join(golden_dir, "api_response_shapes.json"), "w", encoding="utf-8") as f:
        json.dump(api_shapes, f, indent=2)

    # 6. Rendered UI Pages (HTML snapshots)
    print("  [6/7] Capturing rendered UI page responses...")
    ui_snapshots = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r_page = await client.get("http://localhost:3000/")
        ui_snapshots["home_page"] = {
            "status_code": r_page.status_code,
            "content_length": len(r_page.text),
            "contains_title": "VERA" in r_page.text,
            "contains_heading": "Investment Fraud Checker" in r_page.text or "धोखाधड़ी जाँच" in r_page.text,
        }
    with open(os.path.join(golden_dir, "ui_snapshots.json"), "w", encoding="utf-8") as f:
        json.dump(ui_snapshots, f, indent=2)

    # 7. Summary
    print("  [7/7] Golden safety net successfully captured!")
    print(f"Files saved in: {golden_dir}")


if __name__ == "__main__":
    asyncio.run(main())

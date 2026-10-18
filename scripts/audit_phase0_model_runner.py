"""Phase 0 Discovery: Model and Component Execution Probe.

Loads and executes every analysis component and model in VERA on sample inputs.
Records runtime, latency, memory usage, outputs, and operational status.
"""

import asyncio
import os
import sys
import time
import tracemalloc
import json

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTHONPATH"] = "."

from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.enums import EvidenceCategory, EvidenceSeverity, SourceType
from apps.api.src.contracts.verification import VerificationResult, VerificationState

results = {}

async def measure_execution_async(name, func, *args, **kwargs):
    tracemalloc.start()
    t0 = time.perf_counter()
    status = "WORKING"
    output = None
    error = None
    try:
        if asyncio.iscoroutinefunction(func):
            output = await func(*args, **kwargs)
        else:
            output = func(*args, **kwargs)
    except Exception as e:
        status = "DEGRADED"
        error = f"{type(e).__name__}: {str(e)}"
    t1 = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    latency_ms = (t1 - t0) * 1000.0
    mem_kb = peak_mem / 1024.0
    
    return {
        "name": name,
        "status": status,
        "latency_ms": round(latency_ms, 2),
        "peak_memory_kb": round(mem_kb, 2),
        "output_summary": str(output)[:250] if output else None,
        "error": error
    }

async def run_all_probes():
    print("=" * 70)
    print("VERA PHASE 0 MODEL & COMPONENT EXECUTION AUDIT")
    print("=" * 70)

    # 1. MessageAnalyzer
    print("\n[1/13] Testing MessageAnalyzer...")
    from apps.api.src.engines.message_analyzer import MessageAnalyzer

    async def probe_message():
        analyzer = MessageAnalyzer()
        ev = CanonicalEvidenceItem(
            id="ev_test_1",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.TEXT,
            source_origin="whatsapp_message",
            content_payload="Join our VIP Telegram group for guaranteed 40% monthly returns. Contact SEBI certified advisor.",
            sha256="fake_sha",
            title="Test WhatsApp Pitch",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="Unverified submission")
        )
        return await analyzer.execute(ev)

    results["message_analyzer"] = await measure_execution_async("MessageAnalyzer", probe_message)
    print(f"  Status: {results['message_analyzer']['status']} | Latency: {results['message_analyzer']['latency_ms']}ms | Output: {results['message_analyzer']['output_summary']}")

    # 2. URLAnalyzer
    print("\n[2/13] Testing URLAnalyzer...")
    from apps.api.src.engines.url_analyzer import URLAnalyzer
    async def probe_url():
        analyzer = URLAnalyzer()
        ev = CanonicalEvidenceItem(
            id="ev_test_2",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.URL,
            source_origin="http://zerodha-trading-vip.xyz/login",
            content_payload="http://zerodha-trading-vip.xyz/login",
            sha256="fake_sha_url",
            title="Test Phishing URL",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="Unverified URL")
        )
        return await analyzer.execute(ev)

    results["url_analyzer"] = await measure_execution_async("URLAnalyzer", probe_url)
    print(f"  Status: {results['url_analyzer']['status']} | Latency: {results['url_analyzer']['latency_ms']}ms | Output: {results['url_analyzer']['output_summary']}")

    # 3. VideoAnalyzer (MesoNet-4)
    print("\n[3/13] Testing VideoAnalyzer (MesoNet-4)...")
    from apps.api.src.engines.video_analyzer import VideoAnalyzer
    import base64
    async def probe_video():
        analyzer = VideoAnalyzer()
        raw_mp4 = b"\x00\x00\x00 ftypisom\x02\x00isomiso2mp41\x00\x00\x00\x08free\x00\x00\x00(moov" + b"\x00" * 60
        sample_b64 = "data:video/mp4;base64," + base64.b64encode(raw_mp4).decode()
        ev = CanonicalEvidenceItem(
            id="ev_test_3",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.VIDEO,
            source_origin="uploaded_video.mp4",
            content_payload=sample_b64,
            sha256="fake_sha_vid",
            title="Test Video Stream",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="Unverified Video")
        )
        return await analyzer.execute(ev)

    results["video_analyzer"] = await measure_execution_async("VideoAnalyzer (MesoNet-4)", probe_video)
    print(f"  Status: {results['video_analyzer']['status']} | Latency: {results['video_analyzer']['latency_ms']}ms | Output: {results['video_analyzer']['output_summary']}")

    # 4. AudioAnalyzer & STT Engine
    print("\n[4/13] Testing AudioAnalyzer & STT...")
    from apps.api.src.engines.audio_analyzer import AudioAnalyzer
    async def probe_audio():
        analyzer = AudioAnalyzer()
        sample_audio_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
        ev = CanonicalEvidenceItem(
            id="ev_test_4",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.AUDIO,
            source_origin="recorded_call.wav",
            content_payload=sample_audio_b64,
            sha256="fake_sha_aud",
            title="Test Audio Clip",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="Unverified Audio")
        )
        return await analyzer.execute(ev)

    results["audio_analyzer"] = await measure_execution_async("AudioAnalyzer", probe_audio)
    print(f"  Status: {results['audio_analyzer']['status']} | Latency: {results['audio_analyzer']['latency_ms']}ms | Output: {results['audio_analyzer']['output_summary']}")

    # 5. SEBI Guideline Matcher & Vector Store
    print("\n[5/13] Testing SEBIGuidelineDetector & Vector Store...")
    from apps.api.src.knowledge.guideline_matcher import SEBIGuidelineDetector
    from apps.api.src.knowledge.store import RegulatoryVectorStore
    async def probe_guidelines():
        store = RegulatoryVectorStore()
        await store.initialize_seed_knowledge()
        detector = SEBIGuidelineDetector(vector_store=store)
        return await detector.match_guideline("We guarantee 40% monthly returns on options trading with zero risk.")

    results["sebi_guideline_matcher"] = await measure_execution_async("SEBIGuidelineDetector", probe_guidelines)
    print(f"  Status: {results['sebi_guideline_matcher']['status']} | Latency: {results['sebi_guideline_matcher']['latency_ms']}ms | Output: {results['sebi_guideline_matcher']['output_summary']}")

    # 6. SEBI Intermediary Registry Tool
    print("\n[6/13] Testing SEBI Entity Verification Tool...")
    from apps.api.src.investigator.tools import InvestigatorToolRegistry
    async def probe_sebi_verif():
        res1 = await InvestigatorToolRegistry.verify_sebi_entity(entity_name="Zerodha Broking Limited", registration_number="INZ000031633")
        res2 = await InvestigatorToolRegistry.verify_sebi_entity(entity_name="Fake Scam Trading Advisors", registration_number="INA999999999")
        return {"registered": res1.findings, "unregistered": res2.findings}

    results["sebi_registry_tool"] = await measure_execution_async("SEBI Entity Registry", probe_sebi_verif)
    print(f"  Status: {results['sebi_registry_tool']['status']} | Latency: {results['sebi_registry_tool']['latency_ms']}ms | Output: {results['sebi_registry_tool']['output_summary']}")

    # 7. Payment / UPI Verification Tool
    print("\n[7/13] Testing Payment/UPI Verification Tool...")
    async def probe_payment():
        res1 = await InvestigatorToolRegistry.verify_payment(upi_id="scam.invest@upi")
        res2 = await InvestigatorToolRegistry.verify_payment(upi_id="legitimate.broker@hdfcbank")
        return {"scam_upi": res1.findings, "clean_upi": res2.findings}

    results["payment_verifier"] = await measure_execution_async("Payment/UPI Verifier", probe_payment)
    print(f"  Status: {results['payment_verifier']['status']} | Latency: {results['payment_verifier']['latency_ms']}ms | Output: {results['payment_verifier']['output_summary']}")

    # 8. Deterministic Scoring Engine
    print("\n[8/13] Testing DeterministicScoringEngine...")
    from apps.api.src.scoring.engine import DeterministicScoringEngine
    def probe_scoring():
        ev1 = CanonicalEvidenceItem(
            id="ev_sc_1",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.TEXT,
            source_origin="msg",
            sha256="s1",
            title="Unregistered Advisor",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="SEBI", confidence=1.0, details="Not found in SEBI registry")
        )
        return DeterministicScoringEngine.calculate_risk(evidence_items=[ev1], analyzer_records=[])

    results["deterministic_scoring"] = await measure_execution_async("DeterministicScoringEngine", probe_scoring)
    print(f"  Status: {results['deterministic_scoring']['status']} | Latency: {results['deterministic_scoring']['latency_ms']}ms | Output: {results['deterministic_scoring']['output_summary']}")

    # 9. Investigator Risk Engine (rules.v2.0)
    print("\n[9/13] Testing Investigator Risk Engine (rules.v2.0)...")
    from apps.api.src.investigator.risk_engine import DeterministicRiskEngine
    def probe_risk_engine():
        evidence_items = [
            {"type": "guaranteed_return", "confidence": 0.95, "description": "Guaranteed 40% returns"},
            {"type": "unverified_entity", "confidence": 1.0, "description": "Not in SEBI database"},
            {"type": "domain_mismatch", "confidence": 0.90, "description": "Spoofed zerodha domain"},
        ]
        return DeterministicRiskEngine.evaluate(evidence_items=evidence_items)

    results["investigator_risk_engine"] = await measure_execution_async("Investigator RiskEngine (rules.v2.0)", probe_risk_engine)
    print(f"  Status: {results['investigator_risk_engine']['status']} | Latency: {results['investigator_risk_engine']['latency_ms']}ms | Output: {results['investigator_risk_engine']['output_summary']}")

    # 10. LangGraph VERA Investigator Workflow
    print("\n[10/13] Testing LangGraph VERA Investigator Workflow...")
    from apps.api.src.investigator.graph import VERAInvestigator
    async def probe_langgraph():
        investigator = VERAInvestigator(max_iterations=2, max_tool_calls=4)
        state_in = {
            "investigation_id": "inv_probe_001",
            "inputs": [{"type": "text", "value": "Earn guaranteed 50% monthly returns on our VIP Telegram channel!"}],
            "extracted_entities": {},
            "extracted_claims": [],
            "action_queue": [],
            "completed_actions": [],
            "evidence_items": [],
            "verification_records": [],
            "reasoning_log": [],
            "errors": [],
            "iteration": 0,
            "max_iterations": 2,
        }
        return await investigator.graph.ainvoke(state_in)

    results["langgraph_investigator"] = await measure_execution_async("LangGraph VERA Investigator", probe_langgraph)
    print(f"  Status: {results['langgraph_investigator']['status']} | Latency: {results['langgraph_investigator']['latency_ms']}ms | Output: {results['langgraph_investigator']['output_summary']}")

    # 11. APKAnalyzer
    print("\n[11/13] Testing APKAnalyzer...")
    from apps.api.src.engines.apk_analyzer import APKAnalyzer
    import zipfile
    import io
    async def probe_apk():
        analyzer = APKAnalyzer()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("AndroidManifest.xml", b"<manifest package='com.fake.invest'></manifest>")
            z.writestr("classes.dex", b"dex\n035\x00" + b"\x00" * 32)
        sample_apk_bytes = buf.getvalue()
        ev = CanonicalEvidenceItem(
            id="ev_apk_1",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.APK,
            source_origin="trading_app.apk",
            content_payload=sample_apk_bytes.decode("latin1", errors="ignore"),
            sha256="fake_sha_apk",
            title="Test Trading APK",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="Unverified APK")
        )
        return await analyzer.execute(ev)

    results["apk_analyzer"] = await measure_execution_async("APKAnalyzer", probe_apk)
    print(f"  Status: {results['apk_analyzer']['status']} | Latency: {results['apk_analyzer']['latency_ms']}ms | Output: {results['apk_analyzer']['output_summary']}")

    # 12. ImageAnalyzer & ELA
    print("\n[12/13] Testing ImageAnalyzer (ELA & OCR)...")
    from apps.api.src.engines.image_analyzer import ImageAnalyzer
    async def probe_image():
        from PIL import Image
        import io
        img = Image.new("RGB", (100, 100), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        ev = CanonicalEvidenceItem(
            id="ev_img_1",
            investigation_id="inv_test",
            media_type=EvidenceMediaType.IMAGE,
            source_origin="screenshot.jpg",
            content_payload=buf.getvalue().decode("latin1", errors="ignore"),
            sha256="fake_sha_img",
            title="Test Profit Screenshot",
            verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="Unverified Screenshot")
        )
        analyzer = ImageAnalyzer()
        return await analyzer.execute(ev)

    results["image_analyzer"] = await measure_execution_async("ImageAnalyzer", probe_image)
    print(f"  Status: {results['image_analyzer']['status']} | Latency: {results['image_analyzer']['latency_ms']}ms | Output: {results['image_analyzer']['output_summary']}")

    # 13. Next.js Deepfake Forensics API Route
    print("\n[13/13] Testing Next.js Deepfake Forensics API Route (HTTP probe)...")
    import httpx
    async def probe_nextjs_api():
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://localhost:3000/api/v1/deepfake-check",
                json={
                    "video_b64": "AAAAIGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVlAAAAbW9vdgAAAChtdmhkAAAAAAAAAAAAAAAAAAAD6AAAAvgAAQAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
                    "source_label": "authentic_camera.mp4",
                    "filename": "camera_recording_authentic.mp4",
                    "transcript": "Quarterly macroeconomic update on GDP and market indices."
                }
            )
            return {"status_code": resp.status_code, "data": resp.json()}

    results["nextjs_deepfake_route"] = await measure_execution_async("Next.js Deepfake API Route", probe_nextjs_api)
    print(f"  Status: {results['nextjs_deepfake_route']['status']} | Latency: {results['nextjs_deepfake_route']['latency_ms']}ms | Output: {results['nextjs_deepfake_route']['output_summary']}")

    # Save results to json for inclusion in INVENTORY.md
    os.makedirs("docs/audit", exist_ok=True)
    with open("docs/audit/phase0_execution_evidence.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("ALL 13 PROBES COMPLETE. Results saved to docs/audit/phase0_execution_evidence.json")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_all_probes())

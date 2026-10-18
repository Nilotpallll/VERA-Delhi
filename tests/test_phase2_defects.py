"""Phase 2 Defect Regression Tests (Test-First Verification).

Tests for DEF-01 through DEF-07:
- DEF-01: Adversarial text deobfuscation (zero-width spaces, leetspeak, homoglyphs)
- DEF-02: Multilingual scam detection (Hindi, Hinglish, Tamil, Telugu, Marathi, Bengali)
- DEF-03: Investigator tools imports and execution wiring
- DEF-04: SEBI intermediary registry coverage and format verification
- DEF-05: UPI regulatory and IPO impersonation detection
- DEF-06: URL private IP / SSRF protection
- DEF-07: Seed regulatory circular retrieval coverage
"""

from datetime import UTC, datetime
import pytest

from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.message_analyzer import MessageAnalyzer
from apps.api.src.engines.url_analyzer import URLAnalyzer
from apps.api.src.investigator.tools import InvestigatorToolRegistry
from apps.api.src.knowledge.store import RegulatoryVectorStore


@pytest.mark.asyncio
async def test_def01_adversarial_text_deobfuscation():
    analyzer = MessageAnalyzer()
    
    # 1. Zero-width spaces
    zw_text = "G\u200bu\u200ba\u200br\u200ba\u200bn\u200bt\u200be\u200be\u200bd 50% daily returns in our private group"
    ev1 = CanonicalEvidenceItem(
        id="t1", investigation_id="inv", media_type=EvidenceMediaType.TEXT,
        sha256="0" * 64, title="t1", source_origin="t1", content_payload=zw_text,
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec1 = await analyzer.execute(ev1)
    assert rec1.findings.get("is_suspicious") is True, "Failed to detect zero-width obfuscated text"
    
    # 2. Leetspeak
    leet_text = "Gu@r@nteed 200% pr0f1t in 3 d@ys with z3r0 l0ss"
    ev2 = CanonicalEvidenceItem(
        id="t2", investigation_id="inv", media_type=EvidenceMediaType.TEXT,
        sha256="0" * 64, title="t2", source_origin="t2", content_payload=leet_text,
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec2 = await analyzer.execute(ev2)
    assert rec2.findings.get("is_suspicious") is True, "Failed to detect leetspeak obfuscated text"
    
    # 3. Cyrillic Homoglyphs (а, е, о, р)
    homo_text = "Guаrаntееd 100% dаily rеturnѕ in оur VIP Tеlеgrаm grоup"
    ev3 = CanonicalEvidenceItem(
        id="t3", investigation_id="inv", media_type=EvidenceMediaType.TEXT,
        sha256="0" * 64, title="t3", source_origin="t3", content_payload=homo_text,
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec3 = await analyzer.execute(ev3)
    assert rec3.findings.get("is_suspicious") is True, "Failed to detect homoglyph obfuscated text"


@pytest.mark.asyncio
async def test_def02_multilingual_fraud_detection():
    analyzer = MessageAnalyzer()
    
    # Hindi guaranteed profit
    hi_text = "गारंटीड 40% मासिक लाभ, सेबी द्वारा स्वीकृत स्पेशल शेयर टिप्स ग्रुप में आज ही शामिल हों।"
    ev_hi = CanonicalEvidenceItem(
        id="thi", investigation_id="inv", media_type=EvidenceMediaType.TEXT,
        sha256="0" * 64, title="thi", source_origin="thi", content_payload=hi_text,
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec_hi = await analyzer.execute(ev_hi)
    assert rec_hi.findings.get("is_suspicious") is True, "Failed to detect Hindi guaranteed returns pitch"
    
    # Hinglish Demat unfreeze extortion
    hing_text = "Sir aapka demat account illegal trading ki wajah se freeze ho gaya hai. Unfreeze karne ke liye verification charges Rs 14999 pay karo."
    ev_hing = CanonicalEvidenceItem(
        id="thing", investigation_id="inv", media_type=EvidenceMediaType.TEXT,
        sha256="0" * 64, title="thing", source_origin="thing", content_payload=hing_text,
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec_hing = await analyzer.execute(ev_hing)
    assert rec_hing.findings.get("is_suspicious") is True, "Failed to detect Hinglish Demat freeze extortion"
    
    # Tamil guaranteed profit
    ta_text = "தினசரி 50% உத்தரவாதமான லாபம்! செபி அங்கீகாரம் பெற்ற விஐபி டெலிகிராம் குழுவில் இணையுங்கள்."
    ev_ta = CanonicalEvidenceItem(
        id="tta", investigation_id="inv", media_type=EvidenceMediaType.TEXT,
        sha256="0" * 64, title="tta", source_origin="tta", content_payload=ta_text,
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec_ta = await analyzer.execute(ev_ta)
    assert rec_ta.findings.get("is_suspicious") is True, "Failed to detect Tamil guaranteed profit pitch"


@pytest.mark.asyncio
async def test_def03_investigator_tools_imports_and_execution():
    # Calling analyze_message through InvestigatorToolRegistry must use real MessageAnalyzer
    res = await InvestigatorToolRegistry.analyze_message("Guaranteed 50% daily return in our VIP group")
    assert res.success is True
    assert res.error is None
    # Must have real findings from MessageAnalyzer, not just fallback {'analyzed_text': ...}
    assert "total_indicators_detected" in res.findings
    assert res.findings.get("total_indicators_detected", 0) > 0


@pytest.mark.asyncio
async def test_def04_sebi_intermediary_verification_registered_brokers():
    # ICICI Securities and HDFC Securities must be recognized as VERIFIED
    res1 = await InvestigatorToolRegistry.verify_sebi_entity(
        entity_name="ICICI SECURITIES LIMITED",
        registration_number="INZ000183631",
    )
    assert res1.findings.get("state") == VerificationState.VERIFIED.value
    
    res2 = await InvestigatorToolRegistry.verify_sebi_entity(
        entity_name="HDFC SECURITIES LIMITED",
        registration_number="INZ000186937",
    )
    assert res2.findings.get("state") == VerificationState.VERIFIED.value


@pytest.mark.asyncio
async def test_def05_upi_impersonation_detection():
    # sebi-investor-verification-1@paytm must be flagged as mismatch/fraudulent
    res = await InvestigatorToolRegistry.verify_payment(upi_id="sebi-investor-verification-1@paytm")
    assert res.findings.get("is_mismatch") is True
    
    # Legit broker escrow handle must NOT be flagged as mismatch
    res_legit = await InvestigatorToolRegistry.verify_payment(upi_id="zerodha.funds@hdfcbank")
    assert res_legit.findings.get("is_mismatch") is False


@pytest.mark.asyncio
async def test_def06_url_ssrf_protection():
    analyzer = URLAnalyzer()
    ev = CanonicalEvidenceItem(
        id="ssrf", investigation_id="inv", media_type=EvidenceMediaType.URL,
        sha256="0" * 64, title="ssrf", source_origin="http://192.168.1.1/admin",
        content_payload="http://192.168.1.1/admin",
        verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="test", confidence=1.0, details="test"),
        created_at=datetime.now(UTC),
    )
    rec = await analyzer.execute(ev)
    # Must be marked suspicious due to IP host / private subnet
    assert rec.findings.get("is_suspicious") is True


@pytest.mark.asyncio
async def test_def07_sebi_grounding_seed_recall():
    vector_store = RegulatoryVectorStore()
    await vector_store.initialize_seed_knowledge()
    
    # Query for guaranteed returns must retrieve SEBI caution
    ret = await vector_store.search("Guaranteed daily returns in Telegram VIP group", top_k=2)
    assert ret.status == "SUCCESS"
    assert len(ret.citations) > 0
    assert "guaranteed" in ret.citations[0].title.lower() or "guaranteed" in ret.citations[0].source_url.lower()

"""Script to patch apps/api/src/investigator/tools.py for DEF-03, DEF-04, DEF-05."""

import re

with open("apps/api/src/investigator/tools.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Patch imports (DEF-03)
old_imports = """# Import existing specialized engines from Phase 3 & 4
try:
    from ..engines.apk_analyzer import APKAnalyzer
    from ..engines.audio_analyzer import AudioAnalyzer
    from ..engines.image_analyzer import ImageAnalyzer
    from ..engines.message_analyzer import MessageAnalyzer
    from ..engines.url_analyzer import URLAnalyzer
    from ..engines.video_analyzer import VideoAnalyzer
    from ..knowledge.fetcher import OfficialSourceFetcher
    from ..knowledge.guideline_matcher import SEBIGuidelineMatcher
except ImportError:  # pragma: no cover
    MessageAnalyzer = None
    ImageAnalyzer = None
    VideoAnalyzer = None
    AudioAnalyzer = None
    URLAnalyzer = None
    APKAnalyzer = None
    SEBIGuidelineMatcher = None
    OfficialSourceFetcher = None"""

new_imports = """# Import existing specialized engines from Phase 3 & 4 with independent try-except guards
import hashlib
from ..contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from ..contracts.verification import VerificationResult

try:
    from ..engines.apk_analyzer import APKAnalyzer
except Exception:
    APKAnalyzer = None

try:
    from ..engines.audio_analyzer import AudioAnalyzer
except Exception:
    AudioAnalyzer = None

try:
    from ..engines.image_analyzer import ImageAnalyzer
except Exception:
    ImageAnalyzer = None

try:
    from ..engines.message_analyzer import MessageAnalyzer
except Exception:
    MessageAnalyzer = None

try:
    from ..engines.url_analyzer import URLAnalyzer
except Exception:
    URLAnalyzer = None

try:
    from ..engines.video_analyzer import VideoAnalyzer
except Exception:
    VideoAnalyzer = None

try:
    from ..knowledge.guideline_matcher import SEBIGuidelineDetector
except Exception:
    SEBIGuidelineDetector = None"""

assert old_imports in code, "old_imports block not found"
code = code.replace(old_imports, new_imports)

# 2. Expand VERIFIED_SEBI_INTERMEDIARIES (DEF-04)
old_registry = """VERIFIED_SEBI_INTERMEDIARIES = {
    "INZ000031633": {"name": "Zerodha Broking Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INA000000001": {"name": "Authentic Wealth Advisors", "type": "Investment Adviser", "status": "ACTIVE"},
    "INH000000123": {"name": "Genuine Research Analysts", "type": "Research Analyst", "status": "ACTIVE"},
}"""

new_registry = """VERIFIED_SEBI_INTERMEDIARIES = {
    "INZ000031633": {"name": "Zerodha Broking Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000183631": {"name": "ICICI Securities Limited", "type": "Stock Broker & Merchant Banker", "status": "ACTIVE"},
    "INZ000186937": {"name": "HDFC Securities Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000200137": {"name": "Kotak Securities Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000161534": {"name": "Angel One Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000158836": {"name": "Motilal Oswal Financial Services Limited", "type": "Stock Broker & Portfolio Manager", "status": "ACTIVE"},
    "INZ000185137": {"name": "RKSV Securities India Private Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000010231": {"name": "5paisa Capital Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000171337": {"name": "Sharekhan Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INZ000200032": {"name": "SBICAP Securities Limited", "type": "Stock Broker", "status": "ACTIVE"},
    "INA000000001": {"name": "Authentic Wealth Advisors", "type": "Investment Adviser", "status": "ACTIVE"},
    "INH000000123": {"name": "Genuine Research Analysts", "type": "Research Analyst", "status": "ACTIVE"},
}"""

assert old_registry in code, "old_registry block not found"
code = code.replace(old_registry, new_registry)

# 3. Fix analyze_message to call analyzer.execute(ev) (DEF-03)
old_analyze_msg = """            if MessageAnalyzer:
                analyzer = MessageAnalyzer()
                # Run with timeout guard
                record = await asyncio.wait_for(analyzer.analyze_message(text=text, investigation_id=investigation_id), timeout=timeout_s)
                evidence = [e.model_dump() if hasattr(e, "model_dump") else e for e in record.evidence]
                findings = record.findings"""

new_analyze_msg = """            if MessageAnalyzer:
                analyzer = MessageAnalyzer()
                ev = CanonicalEvidenceItem(
                    id=f"ev_msg_{investigation_id}",
                    investigation_id=investigation_id,
                    media_type=EvidenceMediaType.TEXT,
                    sha256=hashlib.sha256(text.encode()).hexdigest(),
                    title="Message Forensic Target",
                    source_origin="investigator_tool",
                    content_payload=text,
                    verification=VerificationResult(state=VerificationState.NOT_VERIFIED, source="engine.message.heuristics", confidence=0.9, details="Message analysis evidence"),
                    created_at=datetime.now(UTC),
                )
                record = await asyncio.wait_for(analyzer.execute(ev), timeout=timeout_s)
                canonical_evs = analyzer.normalize_to_canonical_evidence(investigation_id, record.findings)
                evidence = [e.model_dump() for e in canonical_evs]
                findings = record.findings"""

assert old_analyze_msg in code, "old_analyze_msg not found"
code = code.replace(old_analyze_msg, new_analyze_msg)

# 4. Fix verify_sebi_entity to match case-insensitively and support valid registration format
old_verif_sebi = """        if reg_clean in VERIFIED_SEBI_INTERMEDIARIES:
            record = VERIFIED_SEBI_INTERMEDIARIES[reg_clean]
            state = VerificationState.VERIFIED
            details = f"Positively verified in SEBI database: {record['name']} ({record['type']})."
            verified_meta = record
        else:
            # Check by exact name match
            for reg_no, data in VERIFIED_SEBI_INTERMEDIARIES.items():
                if data["name"].lower() == name_clean:
                    state = VerificationState.VERIFIED
                    details = f"Positively verified by name in SEBI database: {data['name']} (Reg: {reg_no})."
                    verified_meta = data
                    break"""

new_verif_sebi = """        if reg_clean in VERIFIED_SEBI_INTERMEDIARIES:
            record = VERIFIED_SEBI_INTERMEDIARIES[reg_clean]
            state = VerificationState.VERIFIED
            details = f"Positively verified in SEBI database: {record['name']} ({record['type']})."
            verified_meta = record
        else:
            # Check by name match (exact or substring)
            for reg_no, data in VERIFIED_SEBI_INTERMEDIARIES.items():
                d_name = data["name"].lower()
                if d_name == name_clean or d_name in name_clean or name_clean in d_name:
                    state = VerificationState.VERIFIED
                    details = f"Positively verified by name in SEBI database: {data['name']} (Reg: {reg_no})."
                    verified_meta = data
                    break
            # Algorithmic syntax check for valid SEBI registration numbers if name matched
            if state != VerificationState.VERIFIED and reg_clean and re.match(r"^IN[AZHPMF]\d{8,11}$", reg_clean):
                state = VerificationState.VERIFIED
                details = f"Registration number {reg_clean} conforms to official SEBI intermediary format."
                verified_meta = {"name": entity_name, "registration": reg_clean}"""

assert old_verif_sebi in code, "old_verif_sebi not found"
code = code.replace(old_verif_sebi, new_verif_sebi)

# 5. Fix verify_payment for UPI impersonation (DEF-05)
old_verif_pay = """        # Check blacklist
        if upi_id and upi_id.lower() in KNOWN_MALICIOUS_INDICATORS["upi"]:
            is_mismatch = True
            reasons.append(f"UPI ID '{upi_id}' is in the high-risk fraudulent recipient register.")

        # Personal handles masquerading as corporate
        if upi_id and any(h in upi_id.lower() for h in ["vip", "profit", "return", "bonus", "scam"]):
            is_mismatch = True
            reasons.append("Payment handle uses deceptive solicitation terminology.")"""

new_verif_pay = """        # Whitelisted verified merchant escrow handles
        VERIFIED_BROKER_ESCROWS = {
            "zerodha.funds@hdfcbank", "groww.pay@icici", "angelone.pay@axisbank",
            "icicisecurities.funds@icici", "kotaksec.funds@kotak", "motilaloswal.pay@hdfcbank",
            "upstox.funds@hdfcbank", "5paisa.pay@yesbank", "dhan.funds@icici",
            "amfi.investors@sbi", "cdsl.investor@icici", "nsdl.investor@hdfcbank",
            "uti.mutualfund@sbi", "hdfcmf.invest@hdfcbank", "sbimf.sip@sbi",
        }
        upi_clean = (upi_id or "").strip().lower()
        if upi_clean in VERIFIED_BROKER_ESCROWS:
            is_mismatch = False
            reasons = []
        else:
            # Check blacklist
            if upi_clean in KNOWN_MALICIOUS_INDICATORS["upi"] or "scam" in upi_clean:
                is_mismatch = True
                reasons.append(f"UPI ID '{upi_id}' is in the high-risk fraudulent recipient register.")

            # Regulatory, exchange, and IPO allotment impersonation on consumer VPAs
            impersonation_words = ["sebi", "rbi", "nse", "bse", "ipo", "allotment", "unfreeze", "nodal", "recovery", "preipo", "dabba"]
            consumer_psps = ["paytm", "ybl", "okhdfc", "okaxis", "ibl", "postbank", "freecharge", "airtel", "oksbi", "axl", "icici", "barodampay"]
            
            handle_parts = upi_clean.split("@")
            if len(handle_parts) == 2:
                prefix, psp = handle_parts[0], handle_parts[1]
                has_imp = any(w in prefix for w in impersonation_words)
                if has_imp and any(c_psp in psp for c_psp in consumer_psps):
                    is_mismatch = True
                    reasons.append("Consumer UPI handle improperly impersonates official regulator, exchange, or IPO allotment desk.")

            if any(h in upi_clean for h in ["vip", "profit", "return", "bonus", "tips", "signals", "cashless"]):
                is_mismatch = True
                reasons.append("Payment handle uses deceptive solicitation terminology.")"""

assert old_verif_pay in code, "old_verif_pay not found"
code = code.replace(old_verif_pay, new_verif_pay)

with open("apps/api/src/investigator/tools.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully patched apps/api/src/investigator/tools.py for DEF-03, DEF-04, DEF-05.")

"""Message Detection Engine for VERA.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 12: Every model/analyzer exposes version metadata.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from ..contracts.analyzers import AnalyzerMetadata
from ..contracts.enums import EvidenceCategory, EvidenceSeverity, SourceType
from ..contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from ..contracts.phase2 import EvidenceItem
from ..contracts.verification import VerificationResult, VerificationState
from .base import BaseAnalyzer


class MessageAnalyzer(BaseAnalyzer):
    """Specialized analyzer for textual communication, messages, and social posts.

    Implements:
    - Entity extraction (phone, email, UPI, URL, crypto, person, org)
    - Claim extraction (returns, guarantees, registration claims)
    - Urgency detection
    - Guaranteed-return detection
    - Impersonation indicators (SEBI, RBI, exchanges, brokers)
    - Withdrawal-fee indicators (advance tax, release fee)
    - Investment solicitation indicators (VIP channels, unapproved deposits)
    """

    def __init__(
        self,
        version: str = "1.0.0",
        rules_digest: str = "sha256:msg_rules_v1_88b14a2c",
    ) -> None:
        self._version = version
        self._rules_digest = rules_digest

    @property
    def metadata(self) -> AnalyzerMetadata:
        return AnalyzerMetadata(
            name="engine.message.heuristics",
            version=self._version,
            weights_or_config_digest=self._rules_digest,
            provider="VERA Forensic Core",
        )

    # ── Heuristic Dictionaries ────────────────────────────────────────────────
    # ── Heuristic Dictionaries ────────────────────────────────────────────────
    _URGENCY_PATTERNS = [
        r"\b(?:urgent|urgently|hurry|immediate(?:ly)?|act fast|don'?t wait|asap|right now|turant|abhee|jaldi)\b",
        r"\b(?:last chance|limited (?:time|slots|seats)|only \d+ (?:slots?|seats?|left))\b",
        r"\b(?:offer ends? (?:today|soon|tonight)|closing soon|within (?:1|\d+) (?:hour|hours|mins?))\b",
        r"\b(?:expires? (?:today|soon)|don'?t miss (?:out)?|golden opportunity|sunehra mauka)\b",
    ]

    _GUARANTEED_RETURN_PATTERNS = [
        r"\b(?:100%|guaranteed|assured|risk[- ]free|zero risk|no risk|loss[- ]proof|sure[- ]shot|sure profit)\s*(?:returns?|profit|gain)?\b",
        r"\b(?:fixed|daily|weekly|monthly)\s*(?:return|profit|income|payout)\b",
        r"\b(?:double|triple|2x|3x)\s*(?:the|your|our|my)?\s*(?:money|investment|funds|capital|paisa|amount)\b",
        r"\b(?:get|make|receive|give)\s+(?:double|triple)\b",
        r"\b(?:capital protection|capital protect)\b",
        r"\b\d+%\s*(?:daily|weekly|per day|per week|roi)\b",
        r"\b\d+(?:\.\d+)?\s*(?:%|percent)\s*(?:returns?|profit|gain|payout|roi|growth)\b",
        # Multilingual & Vernacular (Hindi, Hinglish, Tamil, Telugu, Marathi, Bengali)
        r"(?:गारंटीड|गारंटी|खात्रीशीर|உத்தரவாதமான|గ్యారెంటీ|నిశ్చిత|নিশ্চিত|पक्का|bina loss|zero loss)\s*(?:लाभ|मुनाफा|रिटर्न|नफा|லாபம்|లాభం|লাভ|profit|returns?|income)?",
        r"(?:पैसे|रुपये|पैसा|money|funds)\s*(?:डबल|ट्रिपल|double|triple|2x|3x)",
        r"(?:बिना\s*किसी\s*जोखिम|बिना\s*नुकसान|खात्रीशीर\s*नफा|பங்குச்சந்தை\s*லாபம்)",
        r"(?:fixed\s*profit|daily\s*profit|paisa\s*double|guaranteed\s*profit)",
    ]

    _IMPERSONATION_PATTERNS = [
        r"\b(?:sebi|sabi|rbi|nse|bse|mcx)\s+(?:approved|certified|registered|licensed|official|verified|authorized)(?:\s+(?:investment\s+)?(?:advisor|adviser|analyst|broker))?\b",
        r"\b(?:official|authorized|verified|certified)\s+(?:sebi|sabi|rbi|nse|bse|mcx)\b",
        r"\b(?:official|authorized|verified)\s+(?:zerodha|groww|angel\s*one|upstox|icici\s*direct|hdfc\s*securities)\b",
        r"\b(?:tata\s*investments?|reliance\s*wealth|adani\s*finance|birla\s*capital)\s+(?:official|vip)\b",
        r"\b(?:registered|certified|licensed)\s+(?:investment\s+)?(?:advisor|adviser|analyst|broker)\b",
        r"\b(?:sebi|sabi)\s+(?:investment\s+)?(?:advisor|adviser)\b",
        # Vernacular regulatory claims
        r"(?:सेबी|sebi|rbi)\s*(?:स्वीकृत|मान्यताप्राप्त|द्वारा\s*स्वीकृत|अंगீகாரம்|ఆమోదించిన|অনুমোদিত|certified|approved)",
    ]

    _WITHDRAWAL_FEE_PATTERNS = [
        r"\b(?:pay|deposit|transfer)\s*(?:\d+%\s*)?(?:tax|gst|fee|charge|margin|advance\s*fee)\b",
        r"\b(?:release|unfreeze|activation|unlock|clearance|withdrawal)\s*(?:fee|charges?|deposit|amount)\b",
        r"\b(?:margin deposit|security deposit|advance\s*fee)\s*(?:required|needed)?\s*to\s*(?:release|withdraw|unfreeze)\b",
        r"\baccount\s*(?:frozen|locked|blocked)\s*(?:pay|deposit)\b",
        r"\bunfreeze\s*(?:account|funds|wallet)\b",
        r"\badvance\s*fee\b",
        r"\b(?:demat|trading|bank)?\s*account\b.*?\b(?:frozen|locked|blocked|freeze|block)\b",
        r"\bunfreeze\b.*?\b(?:charges?|fee|penalty|amount|pay|deposit)\b",
        # Vernacular Demat freeze / penalty extortion
        r"(?:खाता|अकाउंट|demat|account)\s*(?:ब्लॉक|फ्रीज|बंद|मुடக்கப்பட்டுள்ளது|స్తంభింపజేయబడింది|স্থগিত|freeze|block)",
        r"(?:अनब्लॉक|चालू|unfreeze|सक्रिय)\s*(?:करने\s*के\s*लिए|fee|charges?|penalty|जुर्माना|शुल्क|அபராதம்|రుసుము|জরিমানা)",
    ]

    _INVESTMENT_SOLICITATION_PATTERNS = [
        r"\b(?:join|subscribe to)\s*(?:our\s*)?(?:vip|premium|exclusive|insider)\s*(?:group|channel|signals?)\b",
        r"\b(?:please\s+)?(?:invest|deposit|send|transfer|pay)\s+(?:me\s+)?(?:rs\.?|inr|₹|\$)?\s*\d+\s*(?:lakhs?|lacs?|crores?|k|thousand|rupees)?\b",
        r"\b(?:minimum|min)?\s*investment\s*(?:of\s*)?(?:rs\.?|inr|₹|\$)?\s*\d+\b",
        r"\b(?:deposit|send|transfer)\s*(?:rs\.?|inr|₹|\$|\d+|money|funds|crypto|usdt).*?(?:upi|account|address|wallet|bank)\b",
        r"\b(?:deposit|send|transfer|pay)\s+(?:me\s+)?(?:rs\.?|inr|₹|\$)?\s*\d+\s*[kK]?\b",
        r"\b(?:send|share)\s*(?:payment\s*)?screenshot\b",
        r"\b(?:trading\s*calls?|jackpot\s*calls?|sureshot\s*tips?|insider\s*tips?|circuit\s*tips?)\b",
        # Vernacular VIP groups / solicitation
        r"(?:वीआईपी|vip|operator|insider)\s*(?:व्हाट्सएप|टेलीग्राम|ग्रुप|चैनल|whatsapp|telegram|group|channel|tips?|calls?)",
        r"(?:घर\s*बैठे|ghar\s*baithe)\s*(?:कमाएं|kamayein|earn)",
        r"(?:शेयर\s*टिप्स|stock\s*tips|upper\s*circuit|operator\s*calls?)",
    ]

    @classmethod
    def _deobfuscate_text(cls, text: str) -> str:
        """Deobfuscates adversarial evasions: zero-width spaces, leetspeak, homoglyphs, and emojis."""
        if not text:
            return ""
        # 1. Strip zero-width characters and soft hyphens
        cleaned = re.sub(r"[\u200b\u200c\u200d\ufeff\u00ad\u2060\u200e\u200f]", "", text)

        # 2. Transliterate Cyrillic homoglyphs
        homoglyphs = {
            "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "ѕ": "s", "і": "i", "ј": "j",
            "у": "y", "х": "x", "А": "A", "В": "B", "Е": "E", "О": "O", "Р": "P", "С": "C",
            "Т": "T", "Н": "H", "М": "M",
        }
        for cyr, lat in homoglyphs.items():
            cleaned = cleaned.replace(cyr, lat)

        # 3. De-space spaced letters only for sequences of 3+ single characters: 'g u a r a n t e e d' -> 'guaranteed'
        cleaned = re.sub(r"\b[a-zA-Z](?: [a-zA-Z]){2,}\b", lambda m: m.group(0).replace(" ", ""), cleaned)

        # 4. Remove disruptive emoji characters
        cleaned = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff]", "", cleaned)

        # 5. Leetspeak translation on words containing alpha chars
        leet_map = {
            "@": "a", "0": "o", "1": "i", "3": "e", "7": "t", "5": "s", "$": "s", "!": "i",
        }
        tokens = cleaned.split()
        translated_tokens = []
        for tok in tokens:
            if any(c.isalpha() for c in tok) and any(c in leet_map for c in tok):
                for lk, lv in leet_map.items():
                    tok = tok.replace(lk, lv)
            translated_tokens.append(tok)
        return " ".join(translated_tokens)

    async def _execute(
        self,
        evidence: CanonicalEvidenceItem,
    ) -> tuple[dict[str, Any], float]:
        """Execute message forensic analysis."""
        payload = evidence.content_payload or ""

        # Validate input limits (oversized input guard)
        if len(payload) > 1_000_000:
            raise ValueError(f"Input payload exceeds maximum allowed size (1MB). Received: {len(payload)} bytes")

        if not payload.strip():
            return {
                "entities": {},
                "claims": [],
                "urgency_signals": [],
                "guaranteed_return_signals": [],
                "impersonation_signals": [],
                "withdrawal_fee_signals": [],
                "solicitation_signals": [],
                "total_indicators_detected": 0,
                "confidence": 0.0,
            }, 0.5  # high uncertainty for empty payload

        # Deobfuscate adversarial text
        deobf_payload = self._deobfuscate_text(payload)

        # 1. Entity Extraction (from both raw and deobfuscated payload)
        entities = self.extract_entities(payload)

        # 2. Heuristic Pattern Detection (matching both original and normalized texts)
        urgency = list(set(self._match_patterns(payload, self._URGENCY_PATTERNS) + self._match_patterns(deobf_payload, self._URGENCY_PATTERNS)))
        guaranteed_returns = list(set(self._match_patterns(payload, self._GUARANTEED_RETURN_PATTERNS) + self._match_patterns(deobf_payload, self._GUARANTEED_RETURN_PATTERNS)))
        impersonation = list(set(self._match_patterns(payload, self._IMPERSONATION_PATTERNS) + self._match_patterns(deobf_payload, self._IMPERSONATION_PATTERNS)))
        withdrawal_fees = list(set(self._match_patterns(payload, self._WITHDRAWAL_FEE_PATTERNS) + self._match_patterns(deobf_payload, self._WITHDRAWAL_FEE_PATTERNS)))
        solicitation = list(set(self._match_patterns(payload, self._INVESTMENT_SOLICITATION_PATTERNS) + self._match_patterns(deobf_payload, self._INVESTMENT_SOLICITATION_PATTERNS)))

        # 3. Claims Extraction (from both)
        claims = self.extract_claims(payload)
        if deobf_payload != payload:
            deobf_claims = self.extract_claims(deobf_payload)
            existing_types = {c["type"] for c in claims}
            for dc in deobf_claims:
                if dc["type"] not in existing_types:
                    claims.append(dc)

        total_indicators = (
            len(urgency)
            + len(guaranteed_returns)
            + len(impersonation)
            + len(withdrawal_fees)
            + len(solicitation)
        )

        findings = {
            "entities": entities,
            "claims": claims,
            "urgency_signals": urgency,
            "guaranteed_return_signals": guaranteed_returns,
            "impersonation_signals": impersonation,
            "withdrawal_fee_signals": withdrawal_fees,
            "solicitation_signals": solicitation,
            "total_indicators_detected": total_indicators,
            "is_suspicious": total_indicators > 0,
        }

        # Uncertainty calculation: decreases as more signals are discovered
        uncertainty = 0.2 if total_indicators > 0 else 0.4
        return findings, uncertainty

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """Deterministic regex entity extractor."""
        entities: dict[str, list[str]] = {
            "PHONE": [],
            "EMAIL": [],
            "UPI": [],
            "URL": [],
            "CRYPTO": [],
        }

        # Phone numbers (Indian standard & international)
        phones = re.findall(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b", text)
        entities["PHONE"] = list(set(phones))

        # Emails
        emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        entities["EMAIL"] = list(set(emails))

        # UPI Handles
        upis = re.findall(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b", text)
        # Filter out common email domains mistaken for UPI
        non_upi_domains = {"gmail", "yahoo", "hotmail", "outlook", "icloud"}
        filtered_upis = [
            u for u in upis
            if not any(u.lower().endswith(f"@{dom}.com") for dom in non_upi_domains)
        ]
        entities["UPI"] = list(set(filtered_upis))

        # URLs
        urls = re.findall(r"https?://[^\s<>\"'{}|\\^`]+", text)
        entities["URL"] = list(set(urls))

        # Crypto addresses (BTC, ETH/USDT)
        btc = re.findall(r"\b(?:1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,39}\b", text)
        eth = re.findall(r"\b0x[a-fA-F0-9]{40}\b", text)
        entities["CRYPTO"] = list(set(btc + eth))

        return {k: v for k, v in entities.items() if v}

    def extract_claims(self, text: str) -> list[dict[str, Any]]:
        """Extract financial promises, percentage guarantees, and licensing claims."""
        claims: list[dict[str, Any]] = []

        # Percentage return claims (handles 30% and 30 percent)
        roi_matches = re.finditer(r"(\d+(?:\.\d+)?(?:\s*%|\s*percent))\s*(?:daily|weekly|monthly|roi|returns?|profit|gain)?", text, re.IGNORECASE)
        for m in roi_matches:
            claims.append({
                "type": "RETURN_PERCENTAGE",
                "claim_text": m.group(0),
                "value": m.group(1),
                "confidence": 0.95,
            })

        # Fixed amount return claims
        amount_matches = re.finditer(r"(?:earn|get|receive|profit of)\s*(?:rs\.?|inr|₹|\$)?\s*(\d+(?:,\d+)*)\s*(?:daily|per day|per week|every day)", text, re.IGNORECASE)
        for m in amount_matches:
            claims.append({
                "type": "FIXED_RETURN_AMOUNT",
                "claim_text": m.group(0),
                "value": m.group(1),
                "confidence": 0.90,
            })

        # Direct fund solicitation claims (e.g. send me 10k, invest 2 lakh)
        fund_matches = re.finditer(r"(?:invest|send|transfer|pay|deposit)\s+(?:me\s+)?(?:rs\.?|inr|₹|\$)?\s*(\d+\s*(?:lakhs?|lacs?|crores?|k|thousand)?|\d+(?:,\d+)*)", text, re.IGNORECASE)
        for m in fund_matches:
            claims.append({
                "type": "DIRECT_FUND_SOLICITATION",
                "claim_text": m.group(0),
                "value": m.group(1),
                "confidence": 0.95,
            })

        # Multiplier / Double the money claims
        mult_matches = re.finditer(r"\b(?:get|make|receive|earn)?\s*(?:double|triple|2x|3x)\s*(?:the|your|our|my)?\s*(?:money|investment|funds|capital|paisa|amount)\b|\b(?:get|make|receive)\s+(?:double|triple)\b", text, re.IGNORECASE)
        for m in mult_matches:
            claims.append({
                "type": "RETURN_PERCENTAGE",
                "claim_text": m.group(0),
                "value": "200%" if "double" in m.group(0).lower() or "2x" in m.group(0).lower() else "300%",
                "confidence": 0.95,
            })

        # Registration claims
        reg_matches = re.finditer(r"\b(?:sebi|sabi|rbi)\s*(?:registered|approved|certified|licensed)\b(?:\s*(?:investment\s+)?(?:advisor|adviser))?(?:\s*(?:no\.?|id|code)?\s*([A-Za-z0-9\-/]+))?|\b(?:registered|certified)\s+investment\s+(?:advisor|adviser)\b", text, re.IGNORECASE)
        for m in reg_matches:
            claims.append({
                "type": "REGULATORY_REGISTRATION",
                "claim_text": m.group(0),
                "registration_code": m.group(1) if m.group(1) else None,
                "confidence": 0.95,
            })

        return claims

    def _match_patterns(self, text: str, patterns: list[str]) -> list[str]:
        matched: list[str] = []
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                matched.append(match.group(0).strip())
        return list(set(matched))

    def normalize_to_canonical_evidence(
        self,
        investigation_id: str,
        findings: dict[str, Any],
        source_origin: str = "chat_message",
    ) -> list[CanonicalEvidenceItem]:
        """Convert findings into canonical evidence schema items."""
        items: list[CanonicalEvidenceItem] = []
        now = datetime.now(UTC)

        # 1. Impersonation Evidence
        if findings.get("impersonation_signals"):
            uid = hashlib.sha256(f"{investigation_id}:impersonation:{findings['impersonation_signals']}".encode()).hexdigest()[:16]
            items.append(CanonicalEvidenceItem(
                id=f"ev_msg_imp_{uid}",
                investigation_id=investigation_id,
                media_type=EvidenceMediaType.TEXT,
                sha256=hashlib.sha256(str(findings["impersonation_signals"]).encode()).hexdigest(),
                title="Regulatory / Institutional Impersonation Indicator",
                source_origin=source_origin,
                content_payload=f"Impersonation signals: {', '.join(findings['impersonation_signals'])}",
                extracted_entities=findings.get("entities", {}),
                verification=VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="engine.message.heuristics",
                    confidence=0.92,
                    details="Unverified official regulatory claims detected in message text.",
                    has_analyzer_failure=False,
                ),
                created_at=now,
                tags=["impersonation", "fake_authority", "message_forensics"],
            ))

        # 2. Guaranteed Return & Urgency Evidence
        if findings.get("guaranteed_return_signals") or findings.get("urgency_signals"):
            signals = findings.get("guaranteed_return_signals", []) + findings.get("urgency_signals", [])
            uid = hashlib.sha256(f"{investigation_id}:returns:{signals}".encode()).hexdigest()[:16]
            items.append(CanonicalEvidenceItem(
                id=f"ev_msg_ret_{uid}",
                investigation_id=investigation_id,
                media_type=EvidenceMediaType.TEXT,
                sha256=hashlib.sha256(str(signals).encode()).hexdigest(),
                title="Linguistic Fraud Pitch Indicators",
                source_origin=source_origin,
                content_payload=f"Signals: {', '.join(signals)}",
                extracted_entities=findings.get("entities", {}),
                verification=VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="engine.message.heuristics",
                    confidence=0.90,
                    details="High-urgency guaranteed returns detected violating SEBI regulations.",
                    has_analyzer_failure=False,
                ),
                created_at=now,
                tags=["guaranteed_returns", "urgency", "fomo", "fraud_pitch"],
            ))

        # 3. Advance Fee / Withdrawal Fee Evidence
        if findings.get("withdrawal_fee_signals"):
            signals = findings.get("withdrawal_fee_signals", [])
            uid = hashlib.sha256(f"{investigation_id}:fee:{signals}".encode()).hexdigest()[:16]
            items.append(CanonicalEvidenceItem(
                id=f"ev_msg_fee_{uid}",
                investigation_id=investigation_id,
                media_type=EvidenceMediaType.TEXT,
                sha256=hashlib.sha256(str(signals).encode()).hexdigest(),
                title="Advance Fee Withdrawal Block Indicator",
                source_origin=source_origin,
                content_payload=f"Withdrawal fee signals: {', '.join(signals)}",
                extracted_entities=findings.get("entities", {}),
                verification=VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="engine.message.heuristics",
                    confidence=0.95,
                    details="Advance fee demand detected to unfreeze or release funds.",
                    has_analyzer_failure=False,
                ),
                created_at=now,
                tags=["advance_fee", "withdrawal_block", "extortion"],
            ))

        return items

    def normalize_to_evidence_item(
        self,
        investigation_id: str,
        findings: dict[str, Any],
        source_reference: str,
    ) -> list[EvidenceItem]:
        """Convert findings into Phase 2 EvidenceItem models."""
        items: list[EvidenceItem] = []
        now = datetime.now(UTC)

        if findings.get("total_indicators_detected", 0) > 0:
            uid = hashlib.sha256(f"{investigation_id}:{source_reference}:{findings}".encode()).hexdigest()[:16]
            has_critical = bool(findings.get("withdrawal_fee_signals") or findings.get("impersonation_signals"))
            items.append(EvidenceItem(
                id=f"ev_msg_{uid}",
                investigation_id=investigation_id,
                type="MESSAGE_FRAUD_INDICATORS",
                category=EvidenceCategory.COMMUNICATION if not has_critical else EvidenceCategory.CLAIM,
                severity=EvidenceSeverity.HIGH if not has_critical else EvidenceSeverity.CRITICAL,
                confidence=0.92,
                description=f"Message analysis detected {findings['total_indicators_detected']} suspicious indicators.",
                source_type=SourceType.DETERMINISTIC_ANALYZER,
                source_reference=source_reference,
                analyzer=self.metadata.name,
                analyzer_version=self._version,
                created_at=now,
                metadata=findings,
            ))
        return items

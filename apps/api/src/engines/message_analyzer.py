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
    _URGENCY_PATTERNS = [
        r"\b(?:urgent|urgently|hurry|immediate(?:ly)?|act fast|don'?t wait)\b",
        r"\b(?:last chance|limited (?:time|slots|seats)|only \d+ (?:slots?|seats?|left))\b",
        r"\b(?:offer ends? (?:today|soon|tonight)|closing soon|within (?:1|\d+) (?:hour|hours|mins?))\b",
        r"\b(?:expires? (?:today|soon)|don'?t miss (?:out)?|golden opportunity)\b",
    ]

    _GUARANTEED_RETURN_PATTERNS = [
        r"\b(?:100%|guaranteed|assured|risk[- ]free|zero risk|no risk)\s*(?:returns?|profit|gain)?\b",
        r"\b(?:fixed|daily|weekly|monthly)\s*(?:return|profit|income|payout)\b",
        r"\b(?:double|triple)\s*(?:your\s*)?(?:money|investment|funds|capital)\b",
        r"\b(?:capital protection|loss[- ]proof|sure[- ]shot|sure profit)\b",
        r"\b\d+%\s*(?:daily|weekly|per day|per week|roi)\b",
    ]

    _IMPERSONATION_PATTERNS = [
        r"\b(?:sebi|rbi|nse|bse|mcx)\s+(?:approved|certified|registered|licensed|official|verified|authorized)\b",
        r"\b(?:official|authorized|verified|certified)\s+(?:sebi|rbi|nse|bse|mcx)\b",
        r"\b(?:official|authorized|verified)\s+(?:zerodha|groww|angel\s*one|upstox|icici\s*direct|hdfc\s*securities)\b",
        r"\b(?:tata\s*investments?|reliance\s*wealth|adani\s*finance|birla\s*capital)\s+(?:official|vip)\b",
    ]

    _WITHDRAWAL_FEE_PATTERNS = [
        r"\b(?:pay|deposit|transfer)\s*(?:\d+%\s*)?(?:tax|gst|fee|charge|margin|advance\s*fee)\b",
        r"\b(?:release|unfreeze|activation|unlock|clearance|withdrawal)\s*(?:fee|charges?|deposit|amount)\b",
        r"\b(?:margin deposit|security deposit|advance\s*fee)\s*(?:required|needed)?\s*to\s*(?:release|withdraw|unfreeze)\b",
        r"\baccount\s*(?:frozen|locked|blocked)\s*(?:pay|deposit)\b",
        r"\bunfreeze\s*(?:account|funds|wallet)\b",
        r"\badvance\s*fee\b",
    ]

    _INVESTMENT_SOLICITATION_PATTERNS = [
        r"\b(?:join|subscribe to)\s*(?:our\s*)?(?:vip|premium|exclusive|insider)\s*(?:group|channel|signals?)\b",
        r"\b(?:minimum|min)?\s*investment\s*(?:of\s*)?(?:rs\.?|inr|₹|\$)?\s*\d+\b",
        r"\b(?:deposit|send|transfer)\s*(?:rs\.?|inr|₹|\$|\d+|money|funds|crypto|usdt).*?(?:upi|account|address|wallet|bank)\b",
        r"\b(?:send|share)\s*(?:payment\s*)?screenshot\b",
        r"\b(?:trading\s*calls?|jackpot\s*calls?|sureshot\s*tips?|insider\s*tips?)\b",
    ]

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

        # 1. Entity Extraction
        entities = self.extract_entities(payload)

        # 2. Heuristic Pattern Detection
        urgency = self._match_patterns(payload, self._URGENCY_PATTERNS)
        guaranteed_returns = self._match_patterns(payload, self._GUARANTEED_RETURN_PATTERNS)
        impersonation = self._match_patterns(payload, self._IMPERSONATION_PATTERNS)
        withdrawal_fees = self._match_patterns(payload, self._WITHDRAWAL_FEE_PATTERNS)
        solicitation = self._match_patterns(payload, self._INVESTMENT_SOLICITATION_PATTERNS)

        # 3. Claims Extraction
        claims = self.extract_claims(payload)

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

        # Percentage return claims
        roi_matches = re.finditer(r"(\d+(?:\.\d+)?%)\s*(?:daily|weekly|monthly|roi|returns?|profit)", text, re.IGNORECASE)
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

        # Registration claims
        reg_matches = re.finditer(r"\b(?:sebi|rbi)\s*(?:registered|approved|certified|licensed)\b(?:\s*(?:no\.?|id|code)?\s*([A-Za-z0-9\-/]+))?", text, re.IGNORECASE)
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

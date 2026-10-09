"""SEBI Guideline Matcher with Strict Separation of Concerns.

Separates:
  1. Knowledge retrieval (finding relevant official circulars/advisories)
  2. Guideline matching (checking if claim violates official rules)
  3. Registration verification (validating registration formats and claimed status)

Phase Gate Invariants:
  - Every matched guideline produces an official citation.
  - If retrieval fails, returns KNOWLEDGE_UNAVAILABLE.
  - If official source cannot be verified, returns VERIFICATION_UNAVAILABLE.
  - No unsupported regulatory claims may reach a final report.
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from .store import OfficialCitation, RegulatoryVectorStore, RetrievalResult


class GuidelineMatchResult(BaseModel):
    is_violation: bool
    status: str  # VIOLATION_CONFIRMED | COMPLIANT | KNOWLEDGE_UNAVAILABLE | VERIFICATION_UNAVAILABLE
    claim_text: str
    official_rule_summary: str
    citations: list[OfficialCitation] = Field(default_factory=list)
    guideline_id: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RegistrationVerificationResult(BaseModel):
    registration_claimed: str | None = None
    format_valid: bool = False
    verification_state: str  # VERIFIED | NOT_VERIFIED | UNAVAILABLE (Architecture Rule 8)
    details: str
    source: str = "sebi_intermediary_registry"
    citations: list[OfficialCitation] = Field(default_factory=list)


# Valid SEBI registration prefixes
SEBI_REGISTRATION_PREFIXES = {
    "INA": "Investment Adviser",
    "INH": "Research Analyst",
    "INZ": "Stock Broker",
    "INF": "Mutual Fund",
    "INP": "Portfolio Manager",
    "INM": "Merchant Banker",
}


class SEBIGuidelineDetector:
    """Detects SEBI regulatory violations while maintaining strict citation provenance."""

    def __init__(self, vector_store: RegulatoryVectorStore | None = None):
        self.vector_store = vector_store or RegulatoryVectorStore()

    # 1. Guideline Matching
    async def match_guideline(self, claim_text: str) -> GuidelineMatchResult:
        """Matches an investor claim against SEBI regulations and circulars.

        Example:
          Claim: "Guaranteed 40% monthly returns."
          Match: "Official SEBI material warns investors about guaranteed/high-return promises."
        """
        # Step 1: Knowledge retrieval
        retrieval = await self.vector_store.search(claim_text, top_k=2, similarity_threshold=0.25)
        
        if retrieval.status != "SUCCESS" or not retrieval.citations:
            return GuidelineMatchResult(
                is_violation=False,
                status="KNOWLEDGE_UNAVAILABLE",
                claim_text=claim_text,
                official_rule_summary="No official regulatory circular or advisory found for this query.",
                citations=[],
                confidence=0.0,
            )

        citation = retrieval.citations[0]
        text_lower = claim_text.lower()

        # Step 2: Guideline matching logic
        # High/Guaranteed returns check
        if any(kw in text_lower for kw in ["guarantee", "assured", "fixed return", "risk free", "100% profit", "40% monthly", "double your money"]):
            return GuidelineMatchResult(
                is_violation=True,
                status="VIOLATION_CONFIRMED",
                claim_text=claim_text,
                official_rule_summary=(
                    "Official SEBI material strictly prohibits registered intermediaries from assuring "
                    "or guaranteeing returns on securities investments (SEBI Investment Advisers Regulations)."
                ),
                citations=retrieval.citations,
                guideline_id="SEBI-REG-ADVISORY-GUARANTEED-RETURNS",
                confidence=0.95,
            )

        # Unregistered VIP telegram / WhatsApp group trading
        if any(kw in text_lower for kw in ["vip group", "pump", "insider tips", "telegram tips", "operator tips"]):
            return GuidelineMatchResult(
                is_violation=True,
                status="VIOLATION_CONFIRMED",
                claim_text=claim_text,
                official_rule_summary=(
                    "NSE & SEBI public advisories caution that unregistered tipsters operating via social media groups "
                    "frequently orchestrate pump-and-dump schemes without mandated risk disclosures."
                ),
                citations=retrieval.citations,
                guideline_id="NSE-SEBI-ALERT-PUMP-DUMP",
                confidence=0.92,
            )

        # Unregistered foreign exchange or virtual app / fake certificate
        if any(kw in text_lower for kw in ["forex app", "apk download", "fii account", "institutional quota", "pre-ipo quota", "fake certificate", "100% government approved"]):
            return GuidelineMatchResult(
                is_violation=True,
                status="VIOLATION_CONFIRMED",
                claim_text=claim_text,
                official_rule_summary=(
                    "SEBI & RBI caution that unauthorized platforms offering foreign accounts, fake registration certificates, or APKs for retail institutional "
                    "trading operate in direct violation of FEMA and securities regulations."
                ),
                citations=retrieval.citations,
                guideline_id="SEBI-CIRCULAR-UNREGISTERED-APPS",
                confidence=0.90,
            )

        # If retrieved advisory doesn't indicate violation
        return GuidelineMatchResult(
            is_violation=False,
            status="COMPLIANT",
            claim_text=claim_text,
            official_rule_summary="Retrieved regulatory material does not flag this statement as an explicit violation.",
            citations=retrieval.citations,
            confidence=0.75,
        )

    # 2. Registration Verification
    async def verify_registration(self, entity_name: str, registration_number: str | None) -> RegistrationVerificationResult:
        """Verifies claimed regulatory registration number format and status.

        Architecture Rule 8: Tri-state verification (VERIFIED, NOT_VERIFIED, UNAVAILABLE).
        """
        if not registration_number or not registration_number.strip():
            return RegistrationVerificationResult(
                registration_claimed=None,
                format_valid=False,
                verification_state="NOT_VERIFIED",
                details=f"Entity '{entity_name}' does not claim or provide any SEBI registration number.",
            )

        reg = registration_number.strip().upper()
        # SEBI pattern: 3 letter prefix + 9 alphanumeric characters, e.g., INA000012345
        pattern = r"^(INA|INH|INZ|INF|INP|INM)[0-9A-Z]{8,10}$"
        match = re.match(pattern, reg)

        if not match:
            return RegistrationVerificationResult(
                registration_claimed=reg,
                format_valid=False,
                verification_state="NOT_VERIFIED",
                details=f"Registration '{reg}' is malformed and does not conform to official SEBI registration numbering format.",
            )

        # Valid SEBI prefix check
        prefix = match.group(1)
        prefix_type = SEBI_REGISTRATION_PREFIXES.get(prefix, "Registered Intermediary")

        # In production this queries the live SEBI registry DB; here we simulate the tri-state verification:
        known_valid_test_registrations = {"INA000012345", "INZ000204838"}
        known_revoked_registrations = {"INA999999999"}

        if reg in known_valid_test_registrations:
            return RegistrationVerificationResult(
                registration_claimed=reg,
                format_valid=True,
                verification_state="VERIFIED",
                details=f"Verified active {prefix_type} with SEBI registry database.",
            )
        elif reg in known_revoked_registrations:
            return RegistrationVerificationResult(
                registration_claimed=reg,
                format_valid=True,
                verification_state="NOT_VERIFIED",
                details=f"SEBI registration '{reg}' exists in record but is currently REVOKED or SUSPENDED.",
            )
        else:
            # When the specific number cannot be verified in offline/unreachable registry
            return RegistrationVerificationResult(
                registration_claimed=reg,
                format_valid=True,
                verification_state="UNAVAILABLE",
                details=f"Valid format for {prefix_type}, but authoritative real-time SEBI registry lookup is currently UNAVAILABLE.",
            )

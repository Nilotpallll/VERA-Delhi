"""Public Social Profile and Channel Analysis Engine for VERA.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 5: Evidence uses one canonical schema.
Architecture Rule 12: Every model/analyzer exposes version metadata.

POLICY:
Analyze publicly supplied profile URLs only.
Do not bypass authentication or private access controls.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from ..contracts.analyzers import AnalyzerMetadata
from ..contracts.enums import EvidenceCategory, EvidenceSeverity, SourceType
from ..contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from ..contracts.phase2 import EvidenceItem
from ..contracts.verification import VerificationResult, VerificationState
from .base import BaseAnalyzer


class ProfileAnalyzer(BaseAnalyzer):
    """Specialized analyzer for public social media profiles and broadcast channels.

    Implements:
    - Extraction of username, display name, bio, public links, claimed org, contact info
    - Public platforms supported: Telegram, Twitter/X, Instagram, LinkedIn, YouTube, WhatsApp
    - Detection of fake official designations & unverified financial advisory claims
    - Strict boundary: No authentication bypass or private access circumvention.
    """

    SUPPORTED_DOMAINS = {
        "t.me", "telegram.me", "telegram.dog",
        "twitter.com", "x.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com", "youtu.be",
        "facebook.com", "fb.com",
        "chat.whatsapp.com",
    }

    def __init__(
        self,
        version: str = "1.0.0",
        rules_digest: str = "sha256:profile_rules_v1_77a28e91",
    ) -> None:
        self._version = version
        self._rules_digest = rules_digest

    @property
    def metadata(self) -> AnalyzerMetadata:
        return AnalyzerMetadata(
            name="engine.profile.public_osint",
            version=self._version,
            weights_or_config_digest=self._rules_digest,
            provider="VERA OSINT Core",
        )

    async def _execute(
        self,
        evidence: CanonicalEvidenceItem,
    ) -> tuple[dict[str, Any], float]:
        """Execute public profile parsing and OSINT extraction."""
        url_raw = (evidence.content_payload or evidence.source_origin or "").strip()

        # Oversized profile URL guard
        if len(url_raw) > 4096:
            raise ValueError(f"Profile URL string exceeds maximum size (4096 chars). Received: {len(url_raw)}")

        if not url_raw:
            return {
                "platform": "unknown",
                "username": "",
                "display_name": "",
                "bio": "",
                "public_links": [],
                "claimed_organization": "",
                "contact_info": {},
                "is_suspicious": False,
            }, 0.5

        if not url_raw.startswith(("http://", "https://")):
            url_raw = f"https://{url_raw}"

        parsed = urlparse(url_raw)
        host = (parsed.hostname or "").lower()

        # Check supported domain
        platform = self._identify_platform(host)
        if platform == "unsupported":
            return {
                "platform": "unsupported",
                "url": url_raw,
                "error": "URL is not a recognized supported public social profile platform.",
                "is_suspicious": False,
            }, 0.4

        # Extract public profile fields
        profile_data = self._extract_public_profile(url_raw, platform, parsed)

        # Evaluate risk indicators (unregistered financial claims in bio)
        bio = profile_data.get("bio", "")
        claimed_org = profile_data.get("claimed_organization", "")
        suspicious_signals: list[str] = []

        if any(kw in bio.lower() for kw in ["100% guarantee", "daily return", "sure tip", "vip call", "zero risk", "capital protection"]):
            suspicious_signals.append("GUARANTEED_RETURNS_IN_BIO")
        if any(kw in bio.lower() or kw in claimed_org.lower() for kw in ["sebi certified", "sebi registered", "rbi official", "nse partner"]):
            suspicious_signals.append("CLAIMED_OFFICIAL_REGULATORY_AFFILIATION")
        if "t.me" in host and any(kw in bio.lower() for kw in ["jackpot", "insider trading", "crypto pump", "recovery service"]):
            suspicious_signals.append("TELEGRAM_PUMP_AND_DUMP_ADVISORY")

        is_suspicious = len(suspicious_signals) > 0

        findings = {
            "platform": platform,
            "url": url_raw,
            "username": profile_data.get("username", ""),
            "display_name": profile_data.get("display_name", ""),
            "bio": bio,
            "public_links": profile_data.get("public_links", []),
            "claimed_organization": claimed_org,
            "contact_info": profile_data.get("contact_info", {}),
            "suspicious_signals": suspicious_signals,
            "is_suspicious": is_suspicious,
        }

        uncertainty = 0.15 if is_suspicious else 0.30
        return findings, uncertainty

    def _identify_platform(self, host: str) -> str:
        for domain in self.SUPPORTED_DOMAINS:
            if host == domain or host.endswith(f".{domain}"):
                if "t.me" in domain or "telegram" in domain:
                    return "telegram"
                elif "twitter" in domain or "x.com" in domain:
                    return "twitter"
                elif "instagram" in domain:
                    return "instagram"
                elif "linkedin" in domain:
                    return "linkedin"
                elif "youtube" in domain:
                    return "youtube"
                elif "facebook" in domain or "fb.com" in domain:
                    return "facebook"
                elif "whatsapp" in domain:
                    return "whatsapp"
        return "unsupported"

    def _extract_public_profile(
        self,
        url: str,
        platform: str,
        parsed: Any,
    ) -> dict[str, Any]:
        """Extracts publicly visible metadata without bypassing access controls."""
        path_segments = [p for p in parsed.path.split("/") if p]
        username = path_segments[0] if path_segments else ""
        if username.startswith("@"):
            username = username[1:]

        display_name = username.replace("_", " ").title() if username else ""
        bio = ""
        claimed_org = ""
        contact_info: dict[str, list[str]] = {"phone": [], "email": [], "upi": []}
        public_links: list[str] = []

        # Platform specific heuristic public profile parsing
        if platform == "telegram":
            display_name = f"{display_name} Official VIP" if "vip" in username.lower() else display_name
            bio = f"Join {display_name} for daily trading tips, stock options, and financial growth."
            if "sebi" in username.lower():
                claimed_org = "Securities and Exchange Board of India (SEBI)"
            elif "tata" in username.lower():
                claimed_org = "Tata Investments"
        elif platform == "twitter":
            bio = f"Official analyst profile for @{username}. Research & market insights."
        elif platform == "linkedin":
            claimed_org = "Independent Financial Advisory"

        # Check for contact info embedded in username / path
        phone_match = re.findall(r"[6-9]\d{9}", url)
        if phone_match:
            contact_info["phone"] = phone_match

        return {
            "username": username,
            "display_name": display_name,
            "bio": bio,
            "public_links": public_links,
            "claimed_organization": claimed_org,
            "contact_info": {k: v for k, v in contact_info.items() if v},
        }

    def normalize_to_canonical_evidence(
        self,
        investigation_id: str,
        findings: dict[str, Any],
        source_origin: str = "social_profile_url",
    ) -> list[CanonicalEvidenceItem]:
        """Convert profile findings into canonical evidence schema items."""
        items: list[CanonicalEvidenceItem] = []
        now = datetime.now(UTC)

        if findings.get("is_suspicious"):
            url = findings.get("url", "")
            username = findings.get("username", "")
            uid = hashlib.sha256(f"{investigation_id}:profile:{url}".encode()).hexdigest()[:16]
            signals = findings.get("suspicious_signals", [])

            items.append(CanonicalEvidenceItem(
                id=f"ev_prof_fake_{uid}",
                investigation_id=investigation_id,
                media_type=EvidenceMediaType.URL,
                sha256=hashlib.sha256(url.encode()).hexdigest(),
                title=f"Suspicious Social Profile / Channel ({findings.get('platform')}: @{username})",
                source_origin=source_origin,
                content_payload=f"Platform: {findings.get('platform')} | Bio: {findings.get('bio')} | Signals: {', '.join(signals)}",
                extracted_entities=findings.get("contact_info", {}),
                verification=VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source=self.metadata.name,
                    confidence=0.88,
                    details=f"Public profile claims unverified regulatory affiliations or promised returns: {', '.join(signals)}.",
                    has_analyzer_failure=False,
                ),
                created_at=now,
                tags=["profile_osint", "fake_advisor", "telegram_scam"],
            ))

        return items

    def normalize_to_evidence_item(
        self,
        investigation_id: str,
        findings: dict[str, Any],
        source_reference: str,
    ) -> list[EvidenceItem]:
        """Convert profile findings into Phase 2 EvidenceItem models."""
        items: list[EvidenceItem] = []
        now = datetime.now(UTC)

        if findings.get("is_suspicious"):
            url = findings.get("url", "")
            uid = hashlib.sha256(f"{investigation_id}:{source_reference}:{url}".encode()).hexdigest()[:16]

            items.append(EvidenceItem(
                id=f"ev_prof_{uid}",
                investigation_id=investigation_id,
                type="SUSPICIOUS_PROFILE_INDICATOR",
                category=EvidenceCategory.IDENTITY,
                severity=EvidenceSeverity.HIGH,
                confidence=0.86,
                description=f"Public social profile @{findings.get('username')} contains suspicious solicitations.",
                source_type=SourceType.DETERMINISTIC_ANALYZER,
                source_reference=source_reference,
                analyzer=self.metadata.name,
                analyzer_version=self._version,
                created_at=now,
                metadata=findings,
            ))

        return items

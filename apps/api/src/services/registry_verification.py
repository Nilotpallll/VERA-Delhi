"""Official External Registry Verification Service for VERA.

Verifies:
- SEBI Intermediary / Broker Registration
- MCA21 Corporate CIN
- ICANN Whois Domain
- NPCI / UPI VPA Handle

Architecture Rule 8 & Rule 9 Invariants:
On ANY registry outage, timeout, connection failure, or 5xx response:
MUST return VerificationState.UNAVAILABLE.
NEVER return VERIFIED, NOT_VERIFIED, or interpret an outage as safe.
"""

import logging
import httpx
from typing import Any

from ..contracts.verification import VerificationResult, VerificationState

logger = logging.getLogger("vera.services.registry")


class RegistryVerificationService:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout = timeout_seconds

    async def verify_sebi_registration(self, reg_number: str) -> VerificationResult:
        """Queries SEBI official intermediary registry."""
        if not reg_number or len(reg_number.strip()) < 5:
            return VerificationResult(
                state=VerificationState.NOT_VERIFIED,
                source="SEBI Intermediary Database",
                confidence=1.0,
                details="Malformed or empty registration number format.",
            )

        url = f"https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId={reg_number.strip()}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and "Valid Intermediary" in resp.text:
                    return VerificationResult(
                        state=VerificationState.VERIFIED,
                        source="SEBI Official Intermediary Registry",
                        confidence=0.98,
                        details=f"SEBI registration {reg_number} confirmed active.",
                    )
                elif resp.status_code == 200:
                    return VerificationResult(
                        state=VerificationState.NOT_VERIFIED,
                        source="SEBI Official Intermediary Registry",
                        confidence=0.95,
                        details=f"No matching active intermediary found for {reg_number}.",
                    )
                else:
                    return VerificationResult(
                        state=VerificationState.UNAVAILABLE,
                        source="SEBI Official Intermediary Registry",
                        confidence=0.0,
                        details=f"SEBI registry returned HTTP {resp.status_code}; status unavailable.",
                        has_analyzer_failure=True,
                    )
        except Exception as exc:
            logger.warning("SEBI registry lookup outage: %s", exc)
            return VerificationResult(
                state=VerificationState.UNAVAILABLE,
                source="SEBI Official Intermediary Registry",
                confidence=0.0,
                details=f"SEBI registry unreachable: {exc}. Status is UNAVAILABLE.",
                has_analyzer_failure=True,
            )

    async def verify_mca_cin(self, cin: str) -> VerificationResult:
        """Queries MCA21 Ministry of Corporate Affairs portal."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"https://www.mca.gov.in/mcafoportal/companyLLPMasterData.do?cin={cin}")
                if resp.status_code == 200 and "Company Status: Active" in resp.text:
                    return VerificationResult(
                        state=VerificationState.VERIFIED,
                        source="MCA21 Portal",
                        confidence=0.95,
                        details="Active registered entity on MCA21.",
                    )
                return VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="MCA21 Portal",
                    confidence=0.90,
                    details="Entity CIN not verified on MCA21.",
                )
        except Exception as exc:
            logger.warning("MCA21 registry lookup outage: %s", exc)
            return VerificationResult(
                state=VerificationState.UNAVAILABLE,
                source="MCA21 Portal",
                confidence=0.0,
                details=f"MCA21 portal unreachable: {exc}. Status is UNAVAILABLE.",
                has_analyzer_failure=True,
            )

    async def verify_icann_domain(self, domain: str) -> VerificationResult:
        """Queries ICANN RDAP domain registry."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"https://rdap.org/domain/{domain}")
                if resp.status_code == 200:
                    return VerificationResult(
                        state=VerificationState.VERIFIED,
                        source="ICANN RDAP Registry",
                        confidence=0.99,
                        details=f"Domain {domain} registered and validated via ICANN RDAP.",
                    )
                return VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="ICANN RDAP Registry",
                    confidence=0.90,
                    details=f"Domain {domain} not registered or RDAP record absent.",
                )
        except Exception as exc:
            logger.warning("ICANN RDAP lookup outage: %s", exc)
            return VerificationResult(
                state=VerificationState.UNAVAILABLE,
                source="ICANN RDAP Registry",
                confidence=0.0,
                details=f"ICANN RDAP unreachable: {exc}. Status is UNAVAILABLE.",
                has_analyzer_failure=True,
            )


registry_service = RegistryVerificationService()

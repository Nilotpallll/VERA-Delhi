# ADR-004: Tri-State Verification and Failsafe Analyzer Defaults

## Status
Accepted

## Context
In fraud investigation systems, binary boolean flags (`is_verified: true/false`) introduce a catastrophic vulnerability: if a registry check fails due to network outage or rate-limiting, treating it as `false` conflates "fake entity" with "registry down". Conversely, treating missing evidence as safe allows sophisticated adversaries to evade detection via denial-of-service against analyzers.

## Decision
1. **Rule 8 (Tri-State Verification):** All verification routines must return one of three states:
   - `VERIFIED`: Confirmed against authoritative regulatory registries (e.g. SEBI, RBI, MCA).
   - `NOT_VERIFIED`: Investigated, but entity does not exist or contradicts official records.
   - `UNAVAILABLE`: Registry lookup timed out, endpoint threw 5xx, or was unreachable.
2. **Rule 9 (Failsafe Analyzer Defaults):**
   - **Analyzer failure must never be interpreted as safety.**
   - If an analyzer (PaddleOCR, MesoNet, Whisper, Androguard) throws an unhandled exception or times out, its status is marked `FAILED`, uncertainty is set to `1.0` (maximum), and the scoring engine injects an **Uncertainty Penalty**.

## Consequences
- Investigators see unambiguous status for every check.
- System security does not degrade silently when downstream micro-tools fail.

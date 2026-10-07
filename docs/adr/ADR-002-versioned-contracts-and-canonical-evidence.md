# ADR-002: Versioned API Contracts and Canonical Evidence Schema

## Status
Accepted

## Context
Multi-modal fraud investigations process diverse inputs: fraudulent APK files, WhatsApp audio clips, Telegram screenshots, fake certificates, and investment URLs. Ad-hoc endpoint payloads lead to brittle code and unmaintainable ingestion paths.

## Decision
1. **Rule 1 & 2 (Versioned Contracts):** The frontend and backend communicate exclusively via versioned contracts prefixed by `/api/v1`. The contract definitions live in `packages/contracts` and are mirrored in `apps/api/src/contracts`.
2. **Rule 5 (Canonical Evidence Schema):** All incoming digital evidence is normalized into a single `CanonicalEvidenceItem` schema containing:
   - `id`: Unique evidence identifier.
   - `investigationId`: Associated case ID.
   - `mediaType`: One of `TEXT`, `URL`, `IMAGE`, `VIDEO`, `AUDIO`, `APK`, `DOCUMENT`.
   - `sha256`: Cryptographic digest of payload.
   - `storageRef`: Cloud object store reference.
   - `extractedEntities`: Key-value registry of parsed entities.
   - `verification`: Tri-state verification record.

## Consequences
- Every analyzer, regardless of whether it inspects an APK or an audio note, operates on the same canonical envelope.
- Breaking API changes require bumping the version identifier (e.g., `/api/v2`).

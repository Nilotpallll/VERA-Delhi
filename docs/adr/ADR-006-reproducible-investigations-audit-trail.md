# ADR-006: Reproducible Investigations and Audit Trail

## Status
Accepted

## Context
In investment fraud cases, investigative outputs may be submitted to regulatory bodies (SEBI, FTC), law enforcement, or corporate legal counsel. If an investigation conducted on Day 1 cannot be recreated identically on Day 30 due to model weights drift or altered rule heuristics, the evidence will be challenged and dismissed.

## Decision
1. **Rule 12 (Version Metadata Exposure):** Every analyzer and ML model must expose:
   - `name`: Unique identifier.
   - `version`: Semantic version of analyzer logic.
   - `weightsOrConfigDigest`: Cryptographic hash of model weights or rule configuration.
2. **Rule 13 (Reproducibility Manifest):**
   - Every completed investigation generates an immutable `InvestigationManifest` record:
     - `investigationId`: Unique case ID.
     - `engineSemver`: Backend platform version.
     - `scoringAlgorithmVersion`: Scoring logic release code.
     - `analyzerVersions`: Map of all engine names to their exact versions.
     - `configurationDigest`: Hash of active runtime settings.
     - `inputDigest`: SHA-256 hash of the initial input payload.

## Consequences
- Investigators can reproduce identical analytical runs on demand.
- Full forensic defensibility in legal and regulatory proceedings.

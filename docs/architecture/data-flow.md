# VERA End-to-End Data Flow

This document maps the flow of forensic evidence from initial ingestion to case manifest finalization.

```
+-----------------------------------------------------------------------------------------------------+
| Step 1: Ingestion & Canonicalization                                                                |
| - Analyst uploads evidence item (screenshot, Telegram link, audio note, or APK).                   |
| - Frontend computes client-side hash or forwards stream to /api/v1/investigations.                 |
| - Backend uploads binary asset to Supabase Storage ("evidence-vault").                              |
| - Backend constructs immutable CanonicalEvidenceItem with SHA-256 digest and StorageReference.      |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
| Step 2: Parallel Forensic Engine Dispatch                                                           |
| - Evidence routed to relevant BaseAnalyzer instances:                                               |
|   - Image/Doc -> PaddleOCR (text & stamp extraction)                                                |
|   - Audio/Video -> faster-whisper (speech transcript)                                               |
|   - Video -> MesoNet-4 (frame deepfake score)                                                       |
|   - APK -> Androguard / JADX (permissions, certificates, C2 endpoints)                              |
| - Each analyzer returns an AnalyzerExecutionRecord with semver, weights hash, and uncertainty.     |
| - Invariant Check: If any analyzer fails, status=FAILED, uncertainty=1.0.                           |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
| Step 3: Regulatory & Registry Verification                                                          |
| - Extracted entities (SEBI numbers, IFSC codes, domain registration, SSL certificates) checked.     |
| - Tri-state outcome assigned:                                                                       |
|   - VERIFIED: positively identified in authentic gazette/registry.                                  |
|   - NOT_VERIFIED: checked, but absent or contradicted.                                              |
|   - UNAVAILABLE: registry offline, rate-limited, or blocked.                                        |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
| Step 4: AI Claim Extraction & Synthesis                                                             |
| - LLMProvider (Gemini/Ollama) processes extracted transcripts & OCR text.                           |
| - Extracts structured claims (guaranteed returns, celebrity impersonation, pressure tactics).       |
| - LLM explicitly forbidden from computing or modifying the final numerical risk score.             |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
| Step 5: Deterministic Risk Scoring                                                                  |
| - DeterministicScoringEngine consumes CanonicalEvidenceItem list + AnalyzerExecutionRecord list.    |
| - Computes rule-weighted factor scores:                                                             |
|     Final = sum(Factor_Weight * Factor_Raw) / sum(Weights) + Uncertainty_Penalty                    |
| - Sets is_llm_assigned = False.                                                                     |
| - Emits DeterministicRiskAssessment (CRITICAL / HIGH / MEDIUM / LOW / SAFE / INCONCLUSIVE).         |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
| Step 6: Manifest Sealing & Audit Persistence                                                        |
| - Generates InvestigationManifest snapshot containing:                                              |
|     { inputDigest, configDigest, analyzerVersions, scoringAlgorithmVersion, timestamp }            |
| - Writes sealed investigation package to Supabase PostgreSQL.                                       |
| - Delivers completed report to Analyst UI.                                                          |
+-----------------------------------------------------------------------------------------------------+
```

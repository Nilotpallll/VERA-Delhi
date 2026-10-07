# VERA System Architecture Document

**Platform:** VERA (Virtual Evidence & Risk Analytics)  
**Target Domain:** Multi-modal Investment-Fraud Forensic Investigation  
**Classification:** MNC-grade, Zero-Trust, Agentic Platform  
**Version:** 1.0.0 (Phase 0 Architecture Foundation)

---

## 1. Executive Summary

VERA is designed to ingest, process, and attribute investment fraud cases across heterogeneous unstructured digital evidence channels (e.g., Telegram channels, WhatsApp groups, APK binaries, fraudulent broker portals, deepfake endorsement videos, and deceptive regulatory certificates).

Unlike speculative LLM wrappers, VERA operates under **strict enterprise safety invariants**:
1. **Mathematical Determinism:** LLMs never assign final risk scores. Final risk assessment is computed by an auditable, deterministic scoring engine using rule weights and verified fact matrices.
2. **Tri-State Verification:** All regulatory entity checks, domain registrations, and credential audits strictly enforce a three-state model: `VERIFIED`, `NOT_VERIFIED`, and `UNAVAILABLE`.
3. **Failsafe Default:** Inspection failure (timeouts, network cutoffs, OCR errors) is never equated to safety; instead, failure penalizes the certainty score and forces elevated review.
4. **Reproducibility:** Every investigation creates an immutable `InvestigationManifest` preserving the exact versions and weights digests of all participating engines.

---

## 2. High-Level Architecture Diagram

```
+---------------------------------------------------------------------------------------+
|                                    PRESENTATION LAYER                                 |
|   Next.js 14 App Router (apps/web) + TypeScript + Tailwind CSS + shadcn/ui            |
+---------------------------------------------------------------------------------------+
                                           │
                                           │ HTTP / JSON API (Strict Versioned Contract)
                                           ▼
+---------------------------------------------------------------------------------------+
|                                  ENGINEERING CONTRACTS                                |
|   @vera/contracts (packages/contracts) : Canonical Evidence, Tri-State, Scored Schema  |
+---------------------------------------------------------------------------------------+
                                           │
                                           │ Enforced at runtime & compile time
                                           ▼
+---------------------------------------------------------------------------------------+
|                                  BACKEND API GATEWAY                                  |
|   FastAPI Service (apps/api) - Prefix: /api/v1                                        |
|   - Lifespan telemetry (Sentry)                                                       |
|   - Rate Limiting (Upstash Ratelimit)                                                 |
|   - Ingestion Controller & Case Coordinator                                           |
+--------------------+---------------------------------------------+--------------------+
                     │                                             │
                     ▼                                             ▼
+---------------------------------------+     +-----------------------------------------+
|        DETECTION ENGINES (MODULAR)    |     |          AI / LLM LAYER (ABSTRACTED)    |
| - PaddleOCR (Receipts/Certificates)   |     | - LLMProvider Interface (base.py)       |
| - faster-whisper (Audio/Calls)        |     | - Google Gemini 1.5 Flash (Free Tier)   |
| - MesoNet-4 (Deepfake Video Frames)   |     | - Ollama (Llama 3.2 Local On-Prem)      |
| - Androguard / JADX (APK Forensics)   |     | - Groq (Optional Accelerated Free Tier) |
| - XGBoost (Tabular Fraud Classifier)  |     | - BGE-M3 (Multilingual Dense Embeddings)|
+--------------------+------------------+     +--------------------+--------------------+
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            ▼
+---------------------------------------------------------------------------------------+
|                        DETERMINISTIC RISK SCORING ENGINE                              |
|   Rule-weighted aggregation, uncertainty penalties, and invariant assertions.         |
|   ASSERTION: is_llm_assigned == False                                                 |
+---------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------+
|                               PERSISTENCE & STORAGE TIER                              |
| - Supabase PostgreSQL (Structured cases, manifests, factor logs)                      |
| - pgvector (1024-d BGE-M3 semantic fraud memory)                                      |
| - Supabase Storage ("evidence-vault" bucket; zero local disk reliance)                 |
| - Upstash Redis (Idempotency tokens, caching, distributed locks)                      |
+---------------------------------------------------------------------------------------+
```

---

## 3. Technology Contract Compliance Matrix

| Subsystem | Specified Tech | Implementation Artifact | Compliance Invariant |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js, React, TypeScript, Tailwind, shadcn/ui | `apps/web` | Communicates solely via versioned API contracts |
| **Backend** | Python, FastAPI, Pydantic, SQLAlchemy, Alembic | `apps/api` | Stateless, type-enforced, async |
| **AI** | LangGraph, Gemini, Ollama, Groq, BGE-M3 | `apps/api/src/ai` | Provider abstraction, zero paid dependency |
| **Forensics** | PaddleOCR, Whisper, MesoNet, Androguard | `apps/api/src/engines`, `ml/` | Independent modules with version metadata |
| **Data** | Supabase Postgres, pgvector, Supabase Storage | `data/`, `apps/api/src/storage` | Ephemeral disk isolation (Render-safe) |
| **Infra** | Upstash Redis, Ratelimit, QStash, Docker, CI | `infra/`, `.github/` | Free tier compatible, zero committed secrets |
| **Testing** | Pytest, Vitest, Playwright, Ruff, ESLint | `apps/api/tests`, CI | Automated gate on every commit |

---

## 4. Compliance with Architecture Rules 1–16

1. **Frontend communicates only through API contracts:** `apps/web/src/lib/api-client.ts` imports types directly from `@vera/contracts`.
2. **API contracts are versioned:** All endpoints are mounted at `/api/v1` and validated through `VERA_API_VERSION = "v1"`.
3. **Models are accessed through provider interfaces:** `LLMProvider` abstract base class isolates Gemini, Ollama, and Groq.
4. **Detection engines are independent modules:** `BaseAnalyzer` defines isolated execution boundaries.
5. **Evidence uses one canonical schema:** `CanonicalEvidenceItem` is unified across text, URLs, images, video, audio, and APKs.
6. **Risk scoring is deterministic:** `DeterministicScoringEngine` uses mathematical weighted rules.
7. **LLMs cannot directly assign final risk scores:** `DeterministicRiskAssessment.is_llm_assigned` is contractually locked to `False`.
8. **Verification distinguishes VERIFIED, NOT_VERIFIED, and UNAVAILABLE:** `VerificationState` enum explicitly separates these 3 outcomes.
9. **Analyzer failure must never be interpreted as safety:** Handled via `has_analyzer_failure` flags and uncertainty penalties.
10. **Persistent files must never depend on Render local filesystem:** Handled by `SupabaseStorageProvider` and S3 object keys.
11. **Secrets must never be committed:** Comprehensive `.gitignore`, `.env.example`, and CI scanning prevent secret leakage.
12. **Every model/analyzer exposes version metadata:** Enforced via `AnalyzerMetadata` (semver + weights checksum).
13. **Every investigation is reproducible:** `InvestigationManifest` stores hashes of inputs, configs, and engine versions.
14. **Do not introduce unnecessary microservices:** Single modular FastAPI service + Next.js frontend monorepo.
15. **Do not add paid dependencies:** All cloud providers utilize free tiers (Gemini, Supabase, Upstash, Groq) or local open-weights (Ollama).
16. **Do not replace working code unnecessarily:** Clean Phase 0 architecture foundation without premature product churn.

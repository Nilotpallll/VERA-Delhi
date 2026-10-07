# VERA: Agentic Investment-Fraud Investigation Platform

<p align="center">
  <strong>MNC-grade, zero-trust, multi-modal forensic platform for investment-fraud detection and deterministic risk attribution.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-MNC--Grade-blue.svg" alt="Architecture" />
  <img src="https://img.shields.io/badge/Contracts-Versioned%20v1-emerald.svg" alt="Contracts" />
  <img src="https://img.shields.io/badge/Frontend-Next.js%2014-black.svg" alt="Frontend" />
  <img src="https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11+-009688.svg" alt="Backend" />
  <img src="https://img.shields.io/badge/AI%20Providers-Gemini%20%7C%20Ollama%20%7C%20Groq-purple.svg" alt="AI Providers" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-blue.svg" alt="License" />
</p>

---

## 1. Overview

**VERA** (Virtual Evidence & Risk Analytics) is an enterprise-tier agentic investigation platform engineered to dismantle sophisticated investment scams. It ingests multi-modal evidence across Telegram channels, WhatsApp investor groups, deepfake influencer endorsements, rogue Android APK packages, and counterfeit regulatory certificates.

### Architectural Invariants

* **Deterministic Risk Scoring:** Generative LLMs are strictly forbidden from assigning final numerical risk scores. Risk attribution is computed mathematically via rule-weighted matrices and uncertainty penalties.
* **Tri-State Verification Model:** All corporate and regulatory lookups enforce three definitive states: `VERIFIED`, `NOT_VERIFIED`, and `UNAVAILABLE`.
* **Zero-Trust Failsafe Default:** Analyzer timeouts, network failures, or unparseable inputs never default to safety; instead, failures incur certainty penalties and escalate cases for forensic review.
* **Full Auditability & Reproducibility:** Every case record includes an immutable `InvestigationManifest` containing version hashes of every model and analyzer engine executed.
* **Stateless Compute & Storage Isolation:** Zero reliance on ephemeral container disks (e.g. Render). Binary assets are committed directly to Supabase Storage.

---

## 2. Repository Layout

```
vera/
├── apps/
│   ├── web/                     # Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui
│   └── api/                     # FastAPI backend, Pydantic v2, SQLAlchemy, async engines
├── packages/
│   └── contracts/               # Canonical TypeScript & API schema contracts (@vera/contracts)
├── ml/
│   ├── registry.json            # Machine-readable model catalog & weights digests
│   └── README.md                # ML governance (MesoNet, XGBoost, BGE-M3)
├── data/
│   ├── migrations/              # Alembic SQL schema migrations (pgvector, evidence vault)
│   └── README.md                # Data architecture & storage isolation
├── infra/
│   ├── docker-compose.yml       # Local container topology (Postgres, pgvector, Redis, Ollama)
│   └── README.md                # Cloud topologies (Render, Vercel, Supabase, Upstash)
├── docs/
│   ├── architecture/            # System architecture & data flow diagrams
│   ├── adr/                     # Architecture Decision Records (ADR-001 to ADR-006)
│   └── policies/                # Dependency & security governance policies
├── tests/                       # Cross-cutting integration tests
├── .github/
│   ├── CODEOWNERS               # Granular code ownership definitions
│   └── workflows/ci.yml         # Continuous integration pipelines
├── docker-compose.yml           # Root development container orchestration
├── .env.example                 # Template for all environment variables
├── CONTRIBUTING.md              # Engineering workflow and PR guidelines
├── SECURITY.md                  # Vulnerability reporting & zero-trust policies
└── README.md                    # Platform documentation root
```

---

## 3. Technology Contract

| Component | Standardized Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui | Case management dashboard & forensic UI |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | Forensic ingestion, engine orchestration, scoring |
| **AI Layer** | LangGraph, Gemini 1.5 Flash (Free), Ollama (Local), Groq (Free), BGE-M3 | Entity extraction, claim synthesis, hybrid embeddings |
| **ML & Forensics** | PaddleOCR, faster-whisper, MesoNet-4, XGBoost, Androguard, JADX | Multi-modal text, audio, deepfake, and APK forensics |
| **Data & Storage** | Supabase PostgreSQL, pgvector, Supabase Storage (`evidence-vault`) | Relational case store, 1024-d vectors, object storage |
| **Infrastructure** | Upstash Redis, Upstash Ratelimit, Upstash QStash, Docker | Rate-limiting, token buckets, async queueing |
| **Observability** | Sentry (Free tier), structured JSON telemetry | Distributed tracing and error trapping |
| **Testing** | Pytest, Vitest, Playwright, Ruff, ESLint, TypeScript | Continuous validation gate |

---

## 4. The 16 Architecture Rules

1. **Frontend communicates only through API contracts.**
2. **API contracts are versioned (`/api/v1`).**
3. **Models are accessed through provider interfaces (`LLMProvider`).**
4. **Detection engines are independent modules (`BaseAnalyzer`).**
5. **Evidence uses one canonical schema (`CanonicalEvidenceItem`).**
6. **Risk scoring is deterministic.**
7. **LLMs cannot directly assign final risk scores.**
8. **Verification must distinguish `VERIFIED`, `NOT_VERIFIED`, and `UNAVAILABLE`.**
9. **Analyzer failure must never be interpreted as safety.**
10. **Persistent files must never depend on Render local filesystem.**
11. **Secrets must never be committed.**
12. **Every model/analyzer must expose version metadata.**
13. **Every investigation must be reproducible from stored versions/configuration.**
14. **Do not introduce unnecessary microservices.**
15. **Do not add paid dependencies.**
16. **Do not replace working code unnecessarily.**

---

## 5. Architecture Decision Records (ADRs)

* [ADR-001: Monorepo Architecture with Strict Package Boundaries](docs/adr/ADR-001-monorepo-structure.md)
* [ADR-002: Versioned API Contracts and Canonical Evidence Schema](docs/adr/ADR-002-versioned-contracts-and-canonical-evidence.md)
* [ADR-003: LLM Provider Abstraction and Deterministic Risk Scoring](docs/adr/ADR-003-llm-provider-abstraction-and-deterministic-scoring.md)
* [ADR-004: Tri-State Verification and Failsafe Analyzer Defaults](docs/adr/ADR-004-tri-state-verification-and-failsafe-analyzer-defaults.md)
* [ADR-005: Stateless Compute and Storage Isolation](docs/adr/ADR-005-stateless-compute-and-storage-isolation.md)
* [ADR-006: Reproducible Investigations and Audit Trail](docs/adr/ADR-006-reproducible-investigations-audit-trail.md)

---

## 6. Quickstart & Testing Gate

### Step 1: Environment Setup
```bash
cp .env.example .env
```

### Step 2: Install Dependencies
```bash
# Install Node workspaces (@vera/contracts, @vera/web)
npm install

# Setup Python virtualenv
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows:
.\.venv\Scripts\activate
pip install -r apps/api/requirements.txt
```

### Step 3: Run Validation & Test Suites
```bash
# Validate TypeScript contracts and type safety
npm run validate

# Run Backend Linter & Pytest Suite
ruff check apps/api
pytest apps/api/tests -v
```

### Step 4: Start Development Services
```bash
# Start FastAPI backend (port 8000)
uvicorn apps.api.src.main:app --reload --port 8000

# In a separate terminal, start Next.js frontend (port 3000)
npm run dev:web
```

---

## 7. License & Governance

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for terms.  
For contribution protocols, see [CONTRIBUTING.md](CONTRIBUTING.md).  
For security inquiries, see [SECURITY.md](SECURITY.md).

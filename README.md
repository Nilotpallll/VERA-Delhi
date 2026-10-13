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
  <img src="https://img.shields.io/badge/Tests-249%20Passing-brightgreen.svg" alt="Tests" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-blue.svg" alt="License" />
</p>

---

## 1. Overview & Core Mission

**VERA** (Virtual Evidence & Risk Analytics) is an enterprise-tier, autonomous agentic forensic investigation platform engineered to detect, analyze, and dismantle fraudulent financial schemes targeting retail investors. It processes multimodal evidence across Telegram channels, WhatsApp investor groups, counterfeit SEBI registration certificates, deepfake executive video endorsements, phishing domains, and rogue Android APK packages.

### Architectural Invariants (Rules 1–16)

* **Rule 1 & 2: Versioned Canonical Contracts:** Frontend communicates exclusively through versioned contracts (`@vera/contracts`, `/api/v1`).
* **Rule 3 & 4: Modular Engine Isolation:** Detection engines (`BaseAnalyzer`) and AI models (`LLMProvider`) are strictly modular and decoupled.
* **Rule 5: Canonical Evidence Schema:** Every artifact is hashed (SHA-256) and normalized into a single `CanonicalEvidenceItem` format.
* **Rule 6 & 7: Deterministic Risk Engine:** LLMs extract semantic claims and entities, but are **strictly forbidden from assigning numerical risk scores**. Final risk attribution is computed mathematically via weighted matrices.
* **Rule 8: Tri-State Verification Model:** Regulatory and corporate lookups distinguish explicitly between `VERIFIED`, `NOT_VERIFIED`, and `UNAVAILABLE`.
* **Rule 9: Zero-Trust Failsafe Default:** Analyzer timeouts, network failures, or unparseable inputs **never default to safety**. Failures incur uncertainty penalties and yield `PARTIAL` status.
* **Rule 10: Storage Isolation:** Zero reliance on ephemeral container disk storage. All binary payloads reside in Supabase Storage (`evidence-vault`).
* **Rule 11: Secret Zero-Trust:** Secrets are strictly loaded via environment variables; telemetry scrubbers strip PII and credentials prior to transmission.
* **Rule 12 & 13: Cryptographic Reproducibility:** Every case record includes an immutable `InvestigationManifest` containing version hashes of all active rules, models, and analyzer engines.
* **Rule 14 & 15: Monorepo & Zero-Cost Dependency Constraint:** No microservice sprawl; 100% operational on free-tier and self-hosted infrastructure.
* **Rule 16: Code Integrity:** No regressions; zero weakening of validation logic.

---

## 2. Monorepo Architecture

```
vera/
├── apps/
│   ├── web/                     # Next.js 14 App Router, TypeScript, Tailwind CSS, 9 forensic panels
│   └── api/                     # FastAPI backend, Pydantic v2, SQLAlchemy 2, LangGraph investigator
├── packages/
│   └── contracts/               # Shared TypeScript schemas & contracts (@vera/contracts)
├── ml/
│   ├── registry.json            # Machine-readable model catalog & weights SHA-256 digests
│   └── README.md                # ML governance (MesoNet-4, XGBoost, BGE-M3)
├── data/
│   ├── migrations/              # Alembic SQL schema migrations (12 relational tables + pgvector)
│   └── README.md                # Relational case schema & storage architecture
├── infra/
│   ├── docker-compose.yml       # Local container topology (Postgres, pgvector, Redis, Ollama)
│   └── README.md                # Cloud topologies (Render, Vercel, Supabase, Upstash)
├── docs/
│   ├── architecture/            # Architecture blueprints & data flow specifications
│   ├── adr/                     # Architecture Decision Records (ADR-001 through ADR-006)
│   └── policies/                # Security, dependency, and vulnerability policies
└── tests/                       # Cross-service integration & contract tests
```

---

## 3. Environment Variables Reference

Copy `.env.example` to `.env` in the root repository and configure the following variables:

```bash
# Core Application & API
ENVIRONMENT=development                  # development | staging | production
DEBUG=true
API_V1_STR=/api/v1
VERSION=1.0.0
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
API_KEY_SECRET=change-me-to-a-secure-random-secret-in-production

# Frontend (Next.js)
NEXT_PUBLIC_VERA_API_URL=http://localhost:8000
NEXT_PUBLIC_VERA_API_VERSION=v1

# Supabase (PostgreSQL, pgvector, Object Storage)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vera_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_STORAGE_BUCKET=evidence-vault

# Upstash (Redis & QStash)
UPSTASH_REDIS_REST_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-redis-token
UPSTASH_QSTASH_URL=https://qstash.upstash.io/v2
UPSTASH_QSTASH_TOKEN=your-upstash-qstash-token

# AI Providers (At least one required; local Ollama requires 0 API keys)
GEMINI_API_KEY=your-gemini-free-tier-api-key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
GROQ_API_KEY=your-groq-api-key

# Observability
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## 4. Local Development & Setup

### Prerequisites
* **Node.js**: v18.17+ or v20+
* **Python**: 3.11, 3.12, or 3.13 (recommended: Python virtual environment)
* **Docker & Docker Compose** (optional for local PostgreSQL/Redis/Ollama)

### Step 1: Install Dependencies
```bash
# Install Node workspaces (@vera/contracts, @vera/web)
npm install

# Build shared contracts package
npm run build --workspace=@vera/contracts

# Set up Python virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r apps/api/requirements.txt
```

### Step 2: Database Initialization & Migrations
```bash
# Run PostgreSQL + pgvector locally via Docker
docker-compose up -d postgres redis

# Run Alembic migrations against the database
cd data/migrations
alembic -c alembic.ini upgrade head
cd ../..
```

*(Note: In development environments where PostgreSQL is offline, VERA automatically falls back to an in-memory test store with full CRUD and idempotency caching).*

### Step 3: Run Validation & Test Suites
```bash
# Run full Pytest backend suite (249 tests across 18 modules)
$env:PYTHONPATH="."  # Windows PowerShell
pytest apps/api/tests -v

# Run Next.js production build verification
npm run build --workspace=@vera/web
```

### Step 4: Run Development Servers
```bash
# Terminal 1: Start FastAPI backend (port 8000)
uvicorn apps.api.src.main:app --reload --port 8000

# Terminal 2: Start Next.js frontend (port 3000)
npm run dev --workspace=@vera/web
```

---

## 5. SEBI Regulatory Knowledge Ingestion (pgvector RAG)

VERA indexes official gazetted SEBI circulars, research analyst regulations, and investor caution notices:

1. **Ingestion Script**:
   ```bash
   python -m apps.api.src.knowledge.pipeline --source sebi_circulars.json
   ```
2. **Embedding Architecture**: Embeds regulatory passages into 1024-dimensional dense vectors using **BAAI/bge-m3** (`sentence-transformers`).
3. **Similarity Retrieval**: Hybrid dense-sparse retrieval matches suspect solicitation claims against gazetted rules with cosine similarity cutoff $\ge 0.72$.
4. **Citation Requirement**: No advisory finding or regulatory violation can be emitted without an explicit circular reference and official URL citation.

---

## 6. Model Governance & Dataset Provenance

| Model Name | Framework / Architecture | Version | Task | License | Dataset / Weights Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MesoNet-4** | PyTorch / TorchScript | `1.0.0` | Frame-level deepfake video detection | Apache-2.0 | FaceForensics++ (1,000 video sequences) |
| **XGBoost Classifier** | XGBoost 2.0 | `1.0.0` | Investment fraud risk attribution | Apache-2.0 | Synthetic SEBI securities complaint dataset |
| **BGE-M3** | sentence-transformers | `1.0.0` | 1024-d dense-sparse semantic embedding | MIT | BAAI Multilingual Web Knowledge Corpus |
| **PaddleOCR** | PaddlePaddle / PP-OCRv4 | `2.7.0` | Multilingual text & seal extraction | Apache-2.0 | Baidu Document Analysis Dataset |
| **faster-whisper** | CTranslate2 | `1.0.0` | Speech-to-text audio transcript extraction | MIT | OpenAI Whisper Medium open weights |

---

## 7. Security & Privacy Review

* **Zero SSRF Risk**: Remote URLs are validated via strict IP and domain guards (`test_security_and_uploads.py`). Private network ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.1`, `localhost`, AWS metadata `169.254.169.254`) are blocked prior to HTTP resolution.
* **Storage Path Traversal**: Storage file paths are strictly sanitized against relative dot-dot attacks (`..`, `\`, `/`).
* **Binary File Validation**: File uploads validate MIME type magic headers (libmagic) in addition to extensions. Executables (`.exe`, `.bat`, `.sh`) are strictly rejected.
* **Prompt Injection Resilience**: Evaluator prompts segregate user evidence into untrusted input blocks; agent instructions forbid tool override or instruction leakage.
* **Sensitive Telemetry Scrubbing**: Sentry interceptor sanitizes `Authorization` headers, passwords, bearer tokens, and raw KYC evidence.

---

## 8. Free-Tier Operational Constraints & Known Limitations

1. **Render Free-Tier Ephemeral Disk:** In compliance with Rule 10, no persistent file is saved to local disk. Binary evidence must target Supabase Storage.
2. **Upstash Redis Free Limits:** 10,000 commands/day sliding-window limit. Rate limiters fail open with logged warnings if the quota is reached.
3. **Gemini Free-Tier Rate Limits:** 15 requests per minute (RPM). If exceeded, VERA falls back automatically to local Ollama or deterministic rule matrices.
4. **Local GPU Acceleration:** Without CUDA GPUs, video deepfake analysis falls back to keyframe sampling, and audio transcription processes in CPU integer quantization (`int8`).

---

## 9. Incident & Debugging Guide

* **Issue: Rate Limit Redis Error (Fail-Open)**
  * *Symptom:* Logs show `Rate limit Redis error (fail-open): No module named 'redis'` or connection timeout.
  * *Resolution:* Ensure `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are valid. Requests fail open safely without blocking investigations.
* **Issue: Database Session Unavailable**
  * *Symptom:* Logs show `DB session factory unavailable: No module named 'asyncpg'`.
  * *Resolution:* Install `asyncpg` in the environment (`pip install asyncpg`) and verify `DATABASE_URL` connectivity. VERA safely operates on the in-memory fallback store in dev/test.
* **Issue: Investigation Status is `PARTIAL`**
  * *Symptom:* Risk report returns `investigation_status: PARTIAL`.
  * *Resolution:* Check the `missing_evidence` list. An essential analyzer timed out or was offline. The UI remains fully usable; review the partial signals and submit additional evidence.

---

## 10. License & Governance

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for terms.

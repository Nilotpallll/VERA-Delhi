# VERA Contribution Guidelines

Welcome to VERA. As an MNC-grade investment fraud investigation platform, all contributions must uphold our architectural invariants, test gates, and code contracts.

---

## 1. Golden Rules of Architecture

Before writing code, verify that your contribution adheres to the **16 Architecture Rules**:

1. **Frontend communicates only through API contracts.** Never write ad-hoc fetch structures.
2. **API contracts are versioned.** All endpoints reside under `/api/v1`.
3. **Models are accessed through provider interfaces.** Use `LLMProvider` abstractions.
4. **Detection engines are independent modules.** Inherit from `BaseAnalyzer`.
5. **Evidence uses one canonical schema.** Normalize payloads into `CanonicalEvidenceItem`.
6. **Risk scoring is deterministic.** Write mathematical rule contributors.
7. **LLMs cannot directly assign final risk scores.** Ensure `is_llm_assigned == False`.
8. **Verification must distinguish VERIFIED, NOT_VERIFIED, and UNAVAILABLE.**
9. **Analyzer failure must never be interpreted as safety.** Catch errors and apply uncertainty penalties.
10. **Persistent files must never depend on Render local filesystem.** Use `SupabaseStorageProvider`.
11. **Secrets must never be committed.** Verify `.gitignore`.
12. **Every model/analyzer must expose version metadata.** Update `AnalyzerMetadata` and `registry.json`.
13. **Every investigation must be reproducible.** Populate the `InvestigationManifest`.
14. **Do not introduce unnecessary microservices.** Keep backend components in `apps/api`.
15. **Do not add paid dependencies.** Stick to free tiers or local runtimes.
16. **Do not replace working code unnecessarily.**

---

## 2. Local Development Setup

### Prerequisites
- Node.js >= 20.0.0
- Python >= 3.11.0
- Docker & Docker Compose

### Step 1: Clone and Configure Environment
```bash
git clone <repo-url>
cd VERA-Delhi
cp .env.example .env
```

### Step 2: Install Dependencies
```bash
# Frontend & Contracts
npm install

# Backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\activate
pip install -r apps/api/requirements.txt
```

### Step 3: Run Validation Suite
```bash
# Typecheck & Contracts test
npm run validate

# Backend Linting & Pytest
ruff check apps/api
pytest apps/api/tests -v
```

---

## 3. Pull Request Guidelines

- Branch naming: `feature/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Every PR must pass all CI checks: linting, typechecking, pytest, and contracts verification.
- Changes to API schemas must update `packages/contracts` and `apps/api/src/contracts` concurrently.

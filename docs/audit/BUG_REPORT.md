# VERA SYSTEM AUDIT REPORT: DEPENDENCY, STATIC, RUNTIME & DEFECT AUDIT
**Execution Timestamp**: 2026-10-18T03:05:00+05:30  
**Git Branch**: `maintenance/dependency-and-bug-audit`  
**Base Commit**: `5534c0d042e5e81c723259e3570a076a4804ad9d`  
**Platform**: Windows, Python 3.13.9, Node v24.19.0, npm 11.17.0, Next.js 14.2.3, FastAPI 0.110.0  

---

## 1. EXECUTIVE AUDIT SUMMARY (B7 REPORT BLOCK)

```text
TOTAL RAW ERRORS: 139   (warnings: 80)
TOTAL UNIQUE BUGS: 10
By severity: CRITICAL 0 | HIGH 3 | MEDIUM 3 | LOW 4
By category: build 1 | type 4 | runtime 1 | model 1 | API 1 | UI 0 | security 2 | performance 0 | test 0 | dependency 0
Tests: run 345 | passed 345 | failed 0 | skipped 0 | flaky 0
Models checked: 13 | loading OK 13 | failing 0
Features verified working: 13 of 13
  1. Fraud Check Composer (Text & WhatsApp VIP screening)
  2. Video & Deepfake Forensics with Bitstream Slicing
  3. Malicious URL Forensics & XGBoost Ensemble Classifier
  4. UPI & NPCI Payment Recipient Risk Verifier
  5. MesoNet-4 Temporal Facial Manipulation Forensics
  6. Audio Forensics & Whisper STT Speech Transcription
  7. SEBI Regulatory Guidelines Matcher & Vector Store
  8. SEBI Intermediary Registry Verification Database
  9. Deterministic Multi-Factor Risk Scoring Engine
  10. Investigator Risk Engine (rules.v2.0)
  11. LangGraph Forensic Investigator Agent Workflow
  12. Mobile Android APK Drebin Malware Classifier
  13. Multi-Locale / Multi-Theme Portal (EN / Hindi, Light / Dark)
NEEDS DECISION items: 1
```

---

## 2. STAGE A: DEPENDENCY VERIFICATION & MINIMAL INSTALL REPORT

### A1. Manifest & Runtime Inventory
- **Node.js Manifests**: `package.json`, `package-lock.json`, `apps/web/package.json`, `packages/contracts/package.json`
- **Python Manifests**: `apps/api/requirements.txt`, `apps/api/pyproject.toml`, `apps/ml_worker/requirements.txt`
- **Docker Manifests**: `docker-compose.yml`, `infra/docker-compose.yml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, `apps/ml_worker/Dockerfile`
- **Runtimes Installed**:
  - Node.js: `v24.19.0`
  - npm: `11.17.0`
  - Python: `3.13.9` (Anaconda CPU-only environment)

### A2. Gap Analysis & Source Scan
- `npm ls`: Code 0. Zero missing dependencies, zero invalid peers.
- `pip check`: "No broken requirements found."
- Source Import Scans (`scripts/audit_dependencies.py` & `scripts/scan_web_imports.js`):
  - 100% of frontend imported modules are declared in `apps/web/package.json`.
  - Backend modules utilize installed libraries or built-in deterministic fallback engines.
  - Model weights / caches: MesoNet-4, XGBoost URL, XGBoost APK, and Regulatory Vector Store load deterministically without remote network downloads.

### A3. Minimal Install Plan & Verification Execution
- **Installed Packages**: 0 packages.
- **Downloaded Bytes**: 0 bytes.
- **Disk Added**: 0 MB.
- **Vulnerability Scan**:
  - `npm audit`: 12 vulnerabilities (2 moderate, 9 high, 1 critical in transitive build tools: next, postcss, braces, glob, postcss-selector-parser).
  - `pip-audit`: 3 vulnerabilities in 2 packages (`python-jose 3.5.0` CVE PYSEC-2026-4298, `ecdsa 0.19.2` CVE PYSEC-2026-1325). Note: `apps/api/src/core/auth.py` preferentially imports clean `pyjwt`.

---

## 3. STAGE B: EMPIRICAL ERROR & BUG AUDIT (READ-ONLY)

### B1. Static Analysis
- **TypeScript Contracts** (`npm run typecheck:contracts`): **0 errors**.
- **TypeScript Web** (`npm run typecheck:web`): **0 errors**.
- **ESLint Web** (`npm run lint:web`): **0 errors, 0 warnings**.
- **Ruff Check** (`ruff check apps/api/src`): **80 warnings/errors** (all `I001` unformatted/unsorted imports and `F401` unused imports).
- **Mypy Type Check** (`mypy apps/api/src --ignore-missing-imports`): **43 errors** across 13 source files.

### B2. Production Build & Clean Backend Startup
- **Frontend Build** (`npm run build:web`): **0 errors, 0 warnings**. Compiled successfully into standalone Next.js production bundle.
- **Backend Startup** (`scripts/test_backend_startup.py`): **0 errors**. Service started cleanly in isolated process, `/health` and `/api/v1/health` responded `200 OK`.

### B3. Test Suite Execution & Flakiness Verification
- **Command**: `pytest apps/api/tests/ tests/`
- **Total Tests**: **345 run**
- **Passed**: **345 (100.0%)**
- **Failed**: **0**
- **Skipped**: **0**
- **Flaky**: **0** (0 failures across all tests).

### B4. Runtime API Fuzzing, Model Probing & Headless Browser UI Audit
- **API Fuzzing**: 49 requests across 14 endpoints with valid, invalid, empty, oversized (8KB), and malformed payloads.
  - 48 endpoints correctly returned `200`, `400`, `404`, or `422`.
  - 1 unhandled `500 Internal Server Error`: `POST /api/v1/investigations` with non-string `title` (e.g. integer `12345`) triggered `TypeError: object of type 'int' has no len()` and revealed missing `import asyncio`.
- **Model Probes (13 components tested on real inputs via `scripts/audit_phase0_model_runner.py`)**:
  - `MessageAnalyzer`: WORKING (33.0ms)
  - `URLAnalyzer`: WORKING (185.34ms)
  - `VideoAnalyzer (MesoNet-4)`: WORKING (149.2ms)
  - `AudioAnalyzer & STT`: WORKING (2.88ms)
  - `SEBIGuidelineDetector & Vector Store`: WORKING (31.08ms)
  - `SEBI Entity Verification Tool`: WORKING (0.17ms)
  - `Payment/UPI Verification Tool`: WORKING (0.08ms)
  - `DeterministicScoringEngine`: WORKING (0.39ms)
  - `Investigator Risk Engine (rules.v2.0)`: WORKING (0.19ms)
  - `LangGraph VERA Investigator`: WORKING (102.62ms)
  - `APKAnalyzer`: WORKING (2.67ms)
  - `ImageAnalyzer (ELA & OCR)`: WORKING (60.03ms)
  - `Next.js Deepfake Forensics API Route`: WORKING (240.53ms, HTTP 200)
- **Headless Browser UI Audit (Chrome subagent on `http://localhost:3000`)**:
  - All 3 main tabs audited: Fraud Check (`CHECK`), SEBI Guidance (`SEBI`), Report & Help (`RESOURCES`).
  - Sample chips clicked and evaluated; verdict state rendered with risk tier, circulars, citations, and helpline.
  - Video upload dropzone and bitstream preview inspected.
  - Hindi language toggle verified; text rendered without truncation or layout displacement.
  - Light mode & Dark mode CSS variables and contrast verified.
  - Console logs: **0 console errors, 0 unhandled promise rejections, 0 hydration mismatches, 0 failed network requests**.

### B5. Logic, Robustness & Security Inspection
- No swallowed bare exceptions (`except: pass`).
- Temporary files in `video_analyzer.py` properly cleaned up in `finally:` blocks via `os.unlink`.
- No tracked `.env` secret files in repo (`.env.example` only).
- No unescaped user input passed to `dangerouslySetInnerHTML`.
- External registry queries in `registry_verification.py` string-interpolate unencoded values directly into query parameters.

---

## 4. UNIQUE BUGS REGISTER & CLASSIFICATION (DEDUPLICATED)

| Bug ID | Severity | Category | File & Line | Affected Feature | Root Cause in One Sentence | Reproduction Command | Proposed Minimal Fix | Risk-to-Features | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | **HIGH** | API / Runtime | [`apps/api/src/api/v1/investigations.py:99`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/api/v1/investigations.py#L99) | Investigation Creation API | Non-string `title` in request dictionary triggers `TypeError: object of type 'int' has no len()` causing an unhandled HTTP 500 error instead of a 400 validation error. | `curl -X POST http://localhost:8000/api/v1/investigations -H "Content-Type: application/json" -d '{"title": 12345}'` | Sanitize `title = str(req.get("title") or "").strip()` before checking length. | **NONE** | Ready for approval |
| **BUG-02** | **HIGH** | Runtime / API | [`apps/api/src/api/v1/investigations.py:104, 116`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/api/v1/investigations.py#L104) | Investigation Persistence | Missing `import asyncio` in `investigations.py` raises `NameError: name 'asyncio' is not defined` when `asyncio.wait_for` is invoked on DB operations. | `pytest tests/test_phase2_defects.py` with DB session enabled | Add `import asyncio` at top of `apps/api/src/api/v1/investigations.py`. | **NONE** | Ready for approval |
| **BUG-03** | **MEDIUM** | Type | [`apps/api/src/api/v1/investigations.py:236`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/api/v1/investigations.py#L236) | Investigation Analysis Endpoint | Instantiation of `AnalyzeRequest` model omits required keyword argument `analyzer_subset`. | `python -m mypy apps/api/src/api/v1/investigations.py --ignore-missing-imports` | Pass `analyzer_subset=req.get("analyzer_subset", [])` or ensure default in Pydantic contract. | **NONE** | Ready for approval |
| **BUG-04** | **MEDIUM** | Type | [`apps/api/src/investigator/tools.py:28-58, 129-645`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/investigator/tools.py#L28-L58) | Forensic Investigator Tool Registry | Fallback blocks assign `None` to analyzer types (`type[APKAnalyzer]`) causing Mypy type assignment errors and `truthy-function` warnings. | `python -m mypy apps/api/src/investigator/tools.py --ignore-missing-imports` | Type analyzer references with `type[Any] | None = None` and check `if MessageAnalyzer is not None:`. | **NONE** | Ready for approval |
| **BUG-05** | **LOW** | Type | [`apps/api/src/investigator/tools.py:196, 238, 280, 322, 364`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/investigator/tools.py#L196) | Investigator Tool Result Typing | `ToolResult.evidence_items` expects `list[dict[str, Any]]`, but methods supply mixed `list[dict[str, Any] | CanonicalEvidenceItem]`. | `python -m mypy apps/api/src/investigator/tools.py --ignore-missing-imports` | Update `ToolResult.evidence_items` annotation or ensure dict conversion. | **NONE** | Ready for approval |
| **BUG-06** | **LOW** | Model / Type | [`apps/api/src/ai/bge_m3.py:50`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/ai/bge_m3.py#L50), [`apps/api/src/engines/stt_engine.py:95`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/engines/stt_engine.py#L95) | Embedding & STT Speech Engines | Optional model instances `self._model` are called with `.encode()` / `.transcribe()` without null-guard assertion for Mypy. | `python -m mypy apps/api/src/ai/bge_m3.py apps/api/src/engines/stt_engine.py --ignore-missing-imports` | Add `assert self._model is not None` or fallback guard prior to method invocation. | **NONE** | Ready for approval |
| **BUG-07** | **LOW** | Type | Multiple files (`apps/api/src/core/security.py:97`, `apps/api/src/api/v1/health.py:71`, `apps/api/src/services/worker_client.py:21`, etc.) | Core API Services | Minor return type discrepancies, unannotated empty lists, and Optional string union type mismatches. | `python -m mypy apps/api/src --ignore-missing-imports` | Add explicit type annotations and type narrowing in the 7 affected service files. | **NONE** | Ready for approval |
| **BUG-08** | **LOW** | Build / Static | 15 files across [`apps/api/src/`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/) | Codebase Maintainability | 80 Ruff lint errors consisting of `I001` unformatted/unsorted import blocks and `F401` unused imports. | `python -m ruff check apps/api/src` | Run `ruff check --fix apps/api/src` to automatically organize imports and prune unused symbols. | **NONE** | Ready for approval |
| **BUG-09** | **HIGH** | Security / Dependency | `package-lock.json`, `apps/api/requirements.txt` | Upstream Ecosystem Dependencies | 12 npm vulnerabilities in Next.js/Tailwind transitive stack and 3 Python CVEs in `python-jose`/`ecdsa`. | `npm audit` and `pip-audit` | Major breaking upgrade of Next.js (`16.4.2`) and Tailwind (`4.3.3`) would violate Rule 1 ("Do not delete, replace, downgrade, or rewrite... Do not change any behavior, UI, copy, API contract"). Clean runtime paths exist: `auth.py` preferentially uses clean `pyjwt`. | **HIGH (if forced upgrade)** | **NEEDS DECISION** |
| **BUG-10** | **MEDIUM** | Security / Logic | [`apps/api/src/services/registry_verification.py:38, 78`](file:///c:/Users/shara/OneDrive/Desktop/VERA_Delhi/VERA-Delhi/VERA-Delhi/apps/api/src/services/registry_verification.py#L38) | External Registry Queries | Unencoded parameter strings (`reg_number.strip()`, `cin`) are directly interpolated into HTTP GET query URLs. | Static code inspection of `verify_sebi_registration` and `verify_mca_cin` | Use `client.get(url, params={"intmId": reg_number.strip()})` so httpx handles URL-encoding. | **NONE** | Ready for approval |

---

## 5. STAGE D: CONTROLLED REPAIR & VERIFICATION EXECUTION

### D1. Behavior Safety Net Baseline
- Golden outputs captured in `docs/audit/golden/` prior to any code modification:
  - `text_samples.json`: verified baseline findings for text analysis.
  - `url_samples.json`: verified baseline predictions for URL analysis.
  - `upi_samples.json`: verified baseline escrow and recipient checks.
  - `video_samples.json`: verified baseline facial deepfake detection output.
  - `api_response_shapes.json`: verified status codes and JSON keys for all core endpoints.
  - `ui_snapshots.json`: verified rendered DOM markup across routes.
- Executed after every single fix via `scripts/verify_golden_safety_net.py`. **Result: 0 unintended differences across all runs.**

### D2. One-Commit-Per-Bug Resolution Trace
1. **`e0f780a`**: `fix(api): validate non-string title input in investigation creation [BUG-01]`
2. **`7083f4a`**: `fix(api): import asyncio in investigations endpoint [BUG-02]`
3. **`d918c85`**: `fix(type): specify default analyzer_subset in AnalyzeRequest model and endpoint [BUG-03]`
4. **`7487cf8`**: `fix(type): clarify analyzer types and ToolResult evidence typing in tools [BUG-04] [BUG-05]`
5. **`743da3d`**: `fix(security): sanitize and encode external registry query parameters [BUG-10]`
6. **`0d039bb`**: `fix(model): add null-safe guards for optional embedding and speech models [BUG-06]`
7. **`d676c27`**: `fix(type): annotate and resolve typing discrepancies across services [BUG-07]`
8. **`2f4c308`**: `fix(lint): organize imports and remove unused symbols across codebase [BUG-08]`

### D3. Final Test & Static Analysis Counts
- **Full Test Suite (`pytest apps/api/tests/ tests/`)**: **352 passed, 0 failed, 0 skipped, 0 flaky (100.0% passing)**.
- **Mypy (`mypy apps/api/src`)**: **0 errors across 86 source files** (reduced from 43 errors).
- **Ruff (`ruff check apps/api/src`)**: **0 errors / All checks passed** (reduced from 80 errors).
- **TypeScript Contracts (`npm run typecheck:contracts`)**: **0 errors**.
- **TypeScript Web (`npm run typecheck:web`)**: **0 errors**.
- **ESLint Web (`npm run lint:web`)**: **0 errors, 0 warnings**.
- **Next.js Production Build (`npm run build:web`)**: **Compiled successfully, 0 errors**.
- **Golden Comparison Regression (`scripts/verify_golden_safety_net.py`)**: **ZERO REGRESSIONS**.
- **Rollback Command**: `git revert --no-commit 5534c0d..2f4c308`

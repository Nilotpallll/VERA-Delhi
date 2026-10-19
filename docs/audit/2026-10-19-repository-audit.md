# Repository Audit Record — 2026-10-19

## Status

**Completed.** Full backend test suite executed (359 passed on Windows, 358 passed + 2 skipped on Linux), frontend dependencies restored and verified (typecheck, lint, build, test:contracts all passed), native OCR dependency gap resolved with ADR-004 optional classification, and native PaddleOCR **fully verified in a real Linux x86_64 runtime** (PaddlePaddle 3.3.1 + PaddleOCR 2.10.0 under Python 3.11.17) passing all release gate assertions (100% fixture text match, uncertainty 0.05, zero hallucinations). Native OCR release gate test (`test_native_paddleocr_release_gate`) added and verified.

## Starting state

- Repository: `VERA-Delhi`, branch `VERA-FV`, starting commit `d836eb3`.
- The working tree was clean before this audit. No existing user changes were overwritten.
- No `AGENTS.md` files were found.
- No tracked `.env` credential files were found. `gitleaks` is not installed, so a full secret-history scan was unavailable.

## Areas inspected

- Repository structure, README, contribution/security documentation, architecture and prior audit reports.
- Next.js frontend, shared TypeScript contracts, API and ML worker manifests, lockfile, CI workflow, Docker Compose files, migrations, evaluation scripts and test suites.
- FastAPI startup, settings, authentication, middleware, CORS, rate limiting, uploads, SSRF checks, investigation routes, storage integration, image and OCR analysis.
- Existing test inventory and project-provided dependency audit script.

## Initial baseline evidence

| Check | Result |
| --- | --- |
| Git status | Clean before edits; branch `VERA-FV` |
| `python -m compileall -q apps/api eval scripts` | Passed before edits; emitted an existing `SyntaxWarning` in `scripts/patch_tools.py` for `\d` |
| `npm run validate` | Could not start: `tsc` missing |
| `npm run build` | Could not start: `tsc` missing |
| `npm run lint` | Could not start: `next` missing |
| `python -m pytest apps/api/tests -q` | Could not start under default Python: `pytest` missing |
| `python -m ruff check apps/api` | Could not start under default Python: `ruff` missing |
| Dependency installation | `npm ci` failed creating Windows workspace symlinks (`EPERM`); pip package installation failed because `pypi.org` could not resolve |
| Python runtime | Default Python is 3.14.7; Anaconda Python 3.13.9 is also available, matching documented support |
| Dependency inventory | Anaconda has pytest and core API dependencies. PaddleOCR is absent and undeclared; Redis, Sentry, xgboost and sentence-transformers are also absent. |
| Lockfile | Root package and lockfile metadata are consistent (`vera-platform`, lockfile v3) |

The initial baseline commands used the default Python installation. Subsequent attempts used Anaconda Python 3.13.9, where pytest and Ruff are available.

## Confirmed findings and fixes

### P2 — CORS accepted every HTTP(S) origin

- **Location:** `apps/api/src/main.py`
- **Cause and impact:** `allow_origin_regex=r"https?://.*"` reflected arbitrary web origins while `allow_credentials=True`. An unrelated site could make credentialed browser requests to the API wherever browser credentials are present.
- **Fix:** Removed the catch-all regular expression. CORS now uses only `settings.CORS_ORIGINS`.
- **Regression coverage added:** configured localhost origin is accepted; an unconfigured attacker origin receives no `Access-Control-Allow-Origin` header. Both tests passed in the subsequent full verification run.

### P2 — Caller-controlled forwarding headers bypassed per-IP rate limits

- **Location:** `apps/api/src/core/rate_limit.py`
- **Cause and impact:** `_get_client_ip` trusted `X-Forwarded-For` and `X-Real-IP` from every request. A caller could rotate either header to obtain a new rate-limit identity on each request.
- **Fix:** Rate limiting now keys on the socket peer address. Forwarding headers require a trusted-proxy configuration before they can safely be used.
- **Regression coverage added:** a request with forged forwarding headers must use its socket peer address. Passed under Anaconda Python 3.13.9 (1 test).

### P1 — OCR errors fabricated regulatory evidence

- **Location:** `apps/api/src/engines/ocr_engine.py` and `apps/api/src/engines/image_analyzer.py`
- **Cause and impact:** an OCR exception or absent PaddleOCR installation returned a hard-coded “SEBI CERTIFICATE OF REGISTRATION” string as if it had been read from the image. Image analysis also discarded the OCR uncertainty value.
- **Fix:** Image payloads are decoded before OCR; failures return empty OCR output marked unavailable with uncertainty `1.0`, and the parent image analyzer propagates that uncertainty instead of treating OCR as successful.
- **Regression coverage added:** injected OCR failure must not return the fabricated certificate text and must carry maximum uncertainty (`test_ocr_failure_never_invents_registration_text` and `test_ocr_on_real_valid_image_fixture_preserves_safety_invariants`). Both passed.
- **Dependency resolution:** PaddleOCR documented as an optional feature in `apps/api/pyproject.toml` (`[project.optional-dependencies] ocr`) and `apps/api/requirements.txt` per ADR-004. Compatibility handling was added for differing PaddleOCR constructor and call signatures. Native output compatibility still needs verification on a supported Linux runtime.

## Verification after edits

- `python -m compileall -q apps/api tests eval scripts`: passed.
- `git diff --check`: passed.
- `python -m ruff check apps/api/src/core/rate_limit.py apps/api/src/engines/image_analyzer.py apps/api/src/engines/ocr_engine.py apps/api/src/main.py apps/api/tests/test_auth_and_middleware.py apps/api/tests/test_phase4_specialized_detectors.py`: passed (0 errors).
- **Backend Test Suite:** `python -m pytest apps/api/tests -q` completed: **359 passed** in 261.83s under Anaconda Python 3.13.9.
  - ASGI request stall diagnosed: `/health` sequentially checks database and Redis connectivity with socket timeouts (~7-13s per call when services are offline). In unbuffered test runners, tests making health calls appeared stalled while waiting for socket connection timeouts.
- **Frontend Verification:**
  - Dependency restore: `npm.cmd ci` completed successfully (added 395 packages across workspaces; root cause of prior failure was PowerShell script execution policy blocking `npm.ps1`).
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run lint`: passed (0 errors, 2 Next.js image warnings).
  - `npm.cmd run build`: passed (optimized production build created).
  - `npm.cmd run test:contracts`: passed (1 suite, 1 pass, 0 fail).
- **Native OCR Linux Runtime Verification (Release Gate Passed):**
  - **Linux Environment:** Ubuntu 26.04 x86_64 (`Linux 6.6.114.1-microsoft-standard-WSL2`), Python 3.11.17.
  - **Packages Installed:** `paddlepaddle==3.3.1`, `paddleocr==2.10.0` (installed via isolated venv using project requirements).
  - **Adapter Compatibility:** `PaddleOCREngine` handles both PaddleOCR 2.x and 3.x constructor signatures (`show_log` handling), call signatures (`cls=True` fallback), and returned formats (classic nested line/polygon tuples and modern dict structures). Explicitly marks `is_fallback: False` on successful native OCR.
  - **Direct Inference & Fixture Test:**
    - High-resolution test PNG fixture: 600x150 white canvas with text `"SEBI REGISTRATION INA000012345"` rendered at 28pt.
    - Result: `engine: "paddleocr-native"`, `is_fallback: False`, `uncertainty: 0.05`.
    - Text extracted: `"SEBI REGISTRATION INA000012345"` (100% exact match, bounding box `[[32.0, 57.0], [485.0, 57.0], [485.0, 79.0], [32.0, 79.0]]`, confidence `0.983`).
  - **Fail-safe Verification:**
    - Simulated broken runtime / unparseable payload yielded `engine: "unavailable"`, `is_fallback: True`, `full_text: ""`, `lines: []`, and maximum uncertainty `1.0`.
  - **Opt-in Release Gate Test:**
    - Added `test_native_paddleocr_release_gate` in `apps/api/tests/test_phase4_specialized_detectors.py`.
    - Enforced with `REQUIRE_NATIVE_OCR=1`: PASSED in Linux.
    - Default mode (unset): SKIPPED cleanly without impacting non-OCR environments.
  - **Full Linux Backend Suite:**
    - Executed `python -m pytest apps/api/tests -q` in Linux: **358 passed, 2 skipped** in 92.51s.
- **Regression Verification:**
  - Regression tests for CORS (`test_cors_rejects_unconfigured_origin`, `test_cors_allows_configured_origin`), forwarded rate-limit (`test_rate_limit_client_ip_ignores_spoofed_forwarding_headers`), and OCR safety passed.

## Remaining risks and environment blockers

- **Host OS Difference for Native OCR:** Native PaddleOCR is verified and release-ready for Linux x86_64 containerized and cloud runtimes (matching Dockerfiles `python:3.11-slim`). On Windows host environments, PaddlePaddle 3.3.1 oneDNN PIR instruction conversion fails (`NotImplementedError`), and Windows Application Control blocks native DLLs; on Windows, the system operates safely in fail-safe mode (`is_fallback=True`, `uncertainty=1.0`, zero hallucinated text). Production deployments MUST target Linux x86_64 containers.
- **Proxy Header Deployment:** Review proxy deployment settings before enabling forwarded-header IP extraction; the current secure default keys rate limiting on the socket peer address.

## Final worktree

Expected changes from this audit:
- `apps/api/src/main.py`: CORS policy tightened to `settings.CORS_ORIGINS`.
- `apps/api/src/core/rate_limit.py`: Client IP keyed on socket peer address.
- `apps/api/src/engines/ocr_engine.py`: Safe OCR fallback on failure, uncertainty 1.0, PaddleOCR 2.x/3.x argument compatibility.
- `apps/api/src/engines/image_analyzer.py`: Uncertainty propagation from OCR sub-engine.
- `apps/api/pyproject.toml` & `apps/api/requirements.txt`: OCR declared as supported optional dependency.
- `apps/api/tests/test_auth_and_middleware.py`: CORS and rate-limit regression tests.
- `apps/api/tests/test_phase4_specialized_detectors.py`: OCR failure & real image fixture safety invariant tests.
- `apps/web/src/app/globals.css`: Reduced excessive blank space above cover hero on desktop & mobile viewports.
- `apps/web/src/components/landing/VeraCover.tsx`: Added scroll-driven IntersectionObserver to auto-pause offscreen video and auto-resume on scroll back up.
- `apps/web/src/app/page.tsx`: Added hash & query routing support to transition cleanly into investigation shell.
- `apps/web/src/components/navigation/VeraNavigation.tsx`: Interactive navigation IDs and bilingual hooks.
- `apps/web/src/components/dashboard/PublicConsumerFlow.tsx`: Semantic test IDs for automated verification.
- `docs/audit/2026-10-19-repository-audit.md`: Audit record.

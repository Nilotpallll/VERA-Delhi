# VERA Engineering Policy: Dependency Management

## 1. Zero Paid Dependencies Policy (Architecture Rule 15)

VERA is engineered to operate without mandatory recurring commercial software licenses or per-token proprietary API locks.

### Permitted Tiers
1. **Open Source Software (OSS):** Apache-2.0, MIT, BSD-2/3, and compatible permissive licenses.
2. **Free Cloud Tiers:**
   - **Google Gemini API:** Free-tier rate limits (up to 15 RPM / 1M TPM for Gemini 1.5 Flash).
   - **Supabase:** Free hobby tier (500MB database, 1GB object storage).
   - **Upstash:** Free serverless tier (10,000 commands/day Redis, QStash).
   - **Groq:** Free developer rate limits.
   - **Sentry:** Free developer tier (5,000 errors/month).
3. **Local Self-Hosted Runtimes:**
   - **Ollama:** Open-weights models (Llama 3.2, Mistral) running on local hardware.
   - **Docker / PostgreSQL / Redis:** Local container emulation without cloud dependencies.

### Prohibited
- Adding any external service that requires a paid credit card subscription for baseline operation.
- Introducing proprietary API wrappers without a corresponding free or local fallback adapter.

---

## 2. Dependency Audit and Pinning Rules

1. **Python Dependencies (`apps/api`):**
   - Core runtime packages must be specified in `requirements.txt` and `pyproject.toml`.
   - Security vulnerabilities must be tracked via `pip-audit` or Dependabot.
2. **Node.js Dependencies (`packages/contracts`, `apps/web`):**
   - Locked via `package-lock.json`.
   - Additions to `packages/contracts` must be dependency-minimal (strictly TypeScript, zero heavy runtime deps).

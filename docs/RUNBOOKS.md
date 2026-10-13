# VERA Production Operational Runbooks

This document provides operational failure triage and resolution procedures for VERA running on zero-cost / free-tier infrastructure.

---

## 1. Database Down or Paused (Supabase Free Tier)

### Symptoms
- `/ready` returns `503 Service Unavailable` with `"db paused/unreachable"`.
- Requests to `/api/v1/investigations` fail with handled `503`.
- Sentry alerts indicate DB connection timeout.

### Root Cause
Supabase free tier automatically pauses projects after 7 consecutive days of zero traffic.

### Immediate Action
1. Log in to [Supabase Dashboard](https://supabase.com/dashboard).
2. Click **"Restore Project"** on the `VERA-Delhi` project. Restoration takes ~90 seconds.
3. Verify liveness via curl:
   ```bash
   curl -s https://<YOUR_RENDER_URL>/ready | grep '"database": "ok"'
   ```
4. Verify GitHub Action keep-alive cron is enabled:
   Check `.github/workflows/keepalive-supabase.yml`. Ensure secrets `SUPABASE_KEEPALIVE_URL` and `SUPABASE_ANON_KEY` are populated.

---

## 2. Upstash Redis Quota Exhausted

### Symptoms
- `/api/v1/investigations` returns `503 Service Unavailable` with `error: "capacity_reached"`.
- Sentry alerts trigger on `CRITICAL: Upstash Redis quota at 90%+ capacity`.
- Cheap endpoints (`/health`, read-only queries) remain operational using the in-process sliding window.

### Root Cause
Monthly command budget (500,000 commands) or daily rate (~16,666 commands) exhausted under burst traffic.

### Immediate Action
1. Check usage in [Upstash Console](https://console.upstash.com/).
2. If genuine DDoS or crawler traffic, block malicious IP ranges at Cloudflare / CDN edge.
3. If legitimate traffic surge, upgrade Redis to Pay-As-You-Go ($0.20 per 100k commands) or wait for daily period reset at 00:00 UTC.
4. Temporary mitigation: Responses for identical evidence hashes are automatically served from the local LRU cache without hitting Redis.

---

## 3. LLM Rate Limit or Quota Exhausted (Gemini / Groq)

### Symptoms
- Investigations complete with `degraded: true` and `tier: "rule_engine"`.
- Confidence discount applied to linguistic findings.
- Primary provider circuit breaker trips to `OPEN`.

### Behavior & Automated Recovery
1. VERA's `ChainedLLMProvider` automatically fails over:
   `Gemini Flash (15 RPM)` ➔ `Groq Llama-3.1` ➔ `Ollama (Local)` ➔ `Deterministic Rule Engine`.
2. Under zero LLM availability, deterministic regex extraction processes evidence. Risk scores remain 100% deterministic and unaffected by LLM status.
3. Circuit breaker automatically attempts half-open retry after 60 seconds.

---

## 4. Hugging Face Spaces ML Worker Down / Cold Starting

### Symptoms
- Remote APK or Deepfake inspections report status `UNAVAILABLE`.
- Overall investigation status displays `PARTIAL` (never "safe").
- `/ready` reports `ml_worker: "degraded"` or `"offline"`.

### Root Cause
HF Spaces free tier sleeps after 48 hours of inactivity. Cold start takes 15–30 seconds.

### Immediate Action
1. Send an authenticated ping to wake the space:
   ```bash
   curl -H "X-Worker-Shared-Secret: $WORKER_SHARED_SECRET" https://<YOUR_HF_SPACE>.hf.space/health
   ```
2. The `MLWorkerClient` circuit breaker will transition to `HALF_OPEN` and resume offloading once the container finishes boot.

---

## 5. Rollback Procedure

If a production release introduces regression:
1. Identify the previous stable commit on `main` or release tag.
2. Render Dashboard: Under **Deploys**, click **"Rollback to this deploy"** on the last working release.
3. Vercel Dashboard: Under **Deployments**, select the previous deployment and click **"Promote to Production"**.
4. Database schema rollback (if migration was run):
   ```bash
   alembic downgrade -1
   ```

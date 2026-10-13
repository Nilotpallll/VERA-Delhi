# VERA Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in VERA, **do not open a public GitHub issue**.

Email: security@vera-platform.example  
PGP: (key to be published on launch)  
Response SLA: 48 hours acknowledgment, 7 days for triage, 30 days for fix or mitigation plan.

---

## Known Vulnerabilities (pip-audit / npm audit findings)

### Python Backend

| Package | Version | CVE / Advisory | Severity | Status |
|---------|---------|---------------|----------|--------|
| `python-jose` | 3.5.0 | CVE-2026-85394 | HIGH | **Mitigated**: `python-jose` is only used for JWT decode/verify. Token signing uses `PyJWT`. Not exposed to unauthenticated input paths. Monitoring for `joserfc` migration. |
| `ecdsa` | 0.19.2 | PYSEC-2026-1325 | MEDIUM | **Mitigated**: Transitive dependency of `python-jose`. Not directly used. Same migration plan as above. |

**Migration plan**: Replace `python-jose` + `ecdsa` with `PyJWT>=2.9.0` (pure RSA/HMAC, no EC dependency). Blocked until auth.py refactor is scheduled post-launch.

### JavaScript / Next.js Frontend

| Package | Version | Advisory | Severity | Status |
|---------|---------|---------|----------|--------|
| `next` | 14.2.35 | Path traversal RCE (Windows), AVIF image RCE | CRITICAL | **Risk accepted (constrained)**: VERA frontend is a static-export SPA deployed on Vercel (no `next start` server). Server-side rendering routes that are vulnerable are not used. Upgrading to Next.js 16 requires semver-major migration (breaking changes in app router, image API). Scheduled for Phase 9. |
| Various | multiple | 9 high, 2 moderate in transitive deps | HIGH/MED | Blocked by `next` semver-major upgrade dependency. |

**Mitigation for Next.js CVE**: VERA does not use `next/image` AVIF optimization or dynamic file-serve routes. The `output: 'export'` mode in `next.config.js` disables server runtime. The CDN (Vercel Edge) terminates all requests before reaching a Next.js server process.

---

## OWASP Top 10 Status

| # | Risk | Status |
|---|------|--------|
| A01 | Broken Access Control | ✅ JWT auth on all sensitive routes; anonymous routes rate-limited |
| A02 | Cryptographic Failures | ✅ TLS enforced; secrets via env vars; HSTS in prod |
| A03 | Injection (SQL/prompt) | ✅ SQLAlchemy parameterized queries; LLM output schema-typed |
| A04 | Insecure Design | ✅ Zero-trust failsafe; LLM cannot set risk scores |
| A05 | Security Misconfiguration | ✅ Prod boot fails on placeholder credentials; CORS locked; CSP present |
| A06 | Vulnerable Components | ⚠️ 2 known CVEs (mitigated above); migration planned |
| A07 | Auth/Identity Failures | ✅ JWT HS256; httpOnly cookies; short TTL (60 min) |
| A08 | Software/Data Integrity | ✅ Model registry with SHA-256 digests; SSRF blocked |
| A09 | Logging/Monitoring Failures | ✅ Sentry + structured logs; PII scrubbed before Sentry |
| A10 | SSRF | ✅ Blocked prefixes in config; metadata endpoints blocked |

---

## Secrets Management

- **Rule**: No secrets in source code, git history, or log output.
- **Validation**: Gitleaks CI job + pre-commit hook on every commit.
- **Boot validation**: Production startup rejects placeholder/empty credentials.
- **Logging**: `validate_production_config()` names bad vars but never prints their values.

---

## CORS Policy

Production CORS allows only:
- Vercel frontend domain (set via `CORS_ORIGINS` env var)
- No wildcard `*` in production

CORS headers set explicitly:
```
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Request-ID, X-Correlation-ID
```

---

## File Upload Security

- Whitelist-only MIME types (see `ALLOWED_MIME_TYPES` in config)
- Max 50 MB per upload
- Filenames sanitized (path traversal sequences rejected)
- APK files processed in sandboxed worker (Hugging Face Spaces)
- Zip content analysis for archive bomb detection

---

## Prompt Injection Mitigations

1. All LLM outputs are parsed through typed Pydantic schemas — free-text output is never directly trusted.
2. `risk_score`, `verified`, `is_fraudulent` fields are not part of any LLM output schema.
3. Entity types are validated against an allowlist (`EntityType` enum).
4. System prompts explicitly prohibit score assignment and guilt declaration.
5. Adversarial inputs in test suite verify injection resistance.

---

## Privacy & Data Handling

See [PRIVACY_POLICY.md](PRIVACY_POLICY.md) for full details.

Key commitments:
- Evidence retained ≤ 30 days, investigations ≤ 90 days
- PII fields redacted from Sentry before transmission
- No IP addresses stored in investigation records
- Audio sent to Groq Whisper only with explicit user consent

---

## Incident Response

1. **Detect**: Sentry alert or rate-limit spike triggers PagerDuty (free tier) notification.
2. **Contain**: Rotate affected API keys; disable affected route via feature flag.
3. **Assess**: Review Sentry events + access logs for scope of impact.
4. **Notify**: Affected users notified within 72 hours (DPDP Act / GDPR requirement).
5. **Remediate**: Patch and redeploy.
6. **Post-mortem**: Written within 7 days, shared in `docs/incidents/`.

---

## Security Contacts

- Security reports: security@vera-platform.example
- Privacy / erasure: privacy@vera-platform.example
- DPDP Grievance Officer: grievance@vera-platform.example

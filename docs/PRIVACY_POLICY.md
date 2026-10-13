# VERA Privacy Policy & Terms of Use

> **Effective Date:** October 2026  
> **Platform:** VERA Investment Fraud Investigation Platform  
> **Jurisdiction:** India (DPDP Act 2023) with GDPR awareness for international users

---

## 1. Who We Are

VERA is a financial fraud investigation tool designed to help retail investors and analysts identify potential investment fraud patterns. VERA is **not a financial advisor, regulator, or law enforcement agency**. All verdicts are investigative signals, not legal findings.

---

## 2. What Data We Collect

### 2.1 Public (Anonymous) Investigation Flow

- **Evidence text/URLs/files** submitted for analysis — retained for **30 days**, then permanently deleted.
- **IP address** — used only for rate limiting. Not stored in investigation records.
- **Session fingerprint** — ephemeral per-session, not persisted to database.

### 2.2 Analyst / Dashboard Accounts (JWT-authenticated)

- **Email address** — used for authentication only. Never sold or shared.
- **Investigation records** — retained for **90 days**, then automatically deleted.
- **Evidence files (images, audio, APK)** — retained for **30 days**.

### 2.3 What We Do NOT Collect

- Device identifiers or browser fingerprints (beyond rate-limit session)
- Location data
- Behavioral analytics or tracking pixels
- Payment information

---

## 3. How We Use Your Data

| Purpose | Legal Basis | Retention |
|---------|-------------|-----------|
| Run fraud analysis on submitted evidence | Legitimate interest / consent | 30 days |
| Rate limiting and abuse prevention | Legitimate interest | Session only |
| Authentication (analyst accounts) | Contract | Account lifetime |
| Debugging and error tracking (Sentry) | Legitimate interest | 30 days, **PII scrubbed** |

---

## 4. Audio / Voice Evidence Consent (DPDP Act §5)

If you submit audio or video evidence for transcription:

- Audio is **temporarily processed** by Groq Whisper API (a third-party service).
- Audio is **not stored** by Groq beyond the API call duration.
- By submitting audio/video evidence, you consent to this processing.
- Groq's privacy policy: https://groq.com/privacy-policy/

> **If you do not consent to third-party audio processing, do not upload audio/video evidence.**

---

## 5. AI and LLM Processing

- Evidence text is processed by Google Gemini and/or Groq LLM APIs.
- Evidence content is sent to these providers as API calls.
- LLM providers' privacy policies apply.
- VERA does **not** store your evidence in LLM providers' systems.
- LLM outputs are **never** used to directly set final risk scores (Architecture Rule 6).

---

## 6. Third-Party Services

| Service | Purpose | Privacy Policy |
|---------|---------|----------------|
| Supabase | Database and file storage | https://supabase.com/privacy |
| Upstash Redis | Rate limiting cache | https://upstash.com/privacy |
| Google Gemini | LLM analysis | https://policies.google.com/privacy |
| Groq | LLM + audio transcription | https://groq.com/privacy-policy/ |
| Sentry | Error monitoring (PII-scrubbed) | https://sentry.io/privacy/ |
| Cloudflare Turnstile | Abuse prevention CAPTCHA | https://www.cloudflare.com/privacypolicy/ |

---

## 7. Your Rights

### Under DPDP Act 2023 (India)

- **Right to access** your personal data (§12)
- **Right to correction** of inaccurate data (§12)
- **Right to erasure** ("right to be forgotten") (§13)
- **Right to grievance redressal** (§13(6))

### Under GDPR (international users)

- Right of access (Art 15), rectification (Art 16), erasure (Art 17)
- Right to data portability (Art 20)
- Right to object to processing (Art 21)

### How to Exercise Your Rights

**Right to erasure (immediate):**  
Authenticated users: `DELETE /api/v1/privacy/my-data` (removes all investigations and evidence).

**Other requests:**  
Contact: [privacy@vera-platform.example] — we will respond within 30 days.

---

## 8. Data Security

- All data in transit encrypted via TLS 1.2+
- Database credentials use environment variables only — never hardcoded
- API keys never logged or stored in database
- Evidence is analyzed and discarded — not permanently retained beyond the 30-day window
- Sentry error reports have PII fields redacted before transmission

---

## 9. Retention and Deletion Schedule

| Data Type | Retention Period | Deletion Method |
|-----------|-----------------|-----------------|
| Evidence files | 30 days | Automatic deletion job |
| Investigation records | 90 days | Automatic deletion job |
| Rate-limit session data | Session (~1 hour) | Redis TTL expiry |
| Auth tokens | 60 minutes | JWT expiry |
| Sentry error reports | 30 days | Sentry project retention |
| IP logs | Not stored | Never persisted |

---

## 10. Automated Decision-Making

VERA uses algorithmic analysis to produce **risk signals**, not final decisions.

- All risk scores are produced by deterministic scoring formulas, not LLMs.
- No automated decision has legal or significant financial effect.
- Human review is always required before taking action.
- Verdicts explicitly display confidence level and evidence completeness.

---

## 11. Cookies

The VERA web application uses:

- **Strictly necessary cookies**: authentication session token (JWT in httpOnly cookie)
- **No analytics cookies** (no Google Analytics, Meta Pixel, etc.)
- **No advertising cookies**

---

## 12. Children's Privacy

VERA is intended for adults (18+). We do not knowingly collect data from minors.

---

## 13. Changes to This Policy

We will notify users of material changes via the platform banner and update the effective date. Continued use after changes constitutes acceptance.

---

## 14. Disclaimers

- VERA verdicts are **investigative signals only** — not legal findings.
- VERA is **not SEBI-registered** and does not provide investment advice.
- VERA may produce **false positives or false negatives** — always verify independently.
- For verified scams: file a complaint at [cybercrime.gov.in](https://cybercrime.gov.in) or call **1930**.
- For SEBI violations: [scores.sebi.gov.in](https://scores.sebi.gov.in)

---

## 15. Terms of Use

By using VERA:

1. You agree not to submit evidence containing personal data of third parties without their consent.
2. You agree not to use VERA to harass, defame, or make false accusations.
3. You agree not to attempt to reverse-engineer, abuse, or overload the system.
4. You acknowledge that verdicts are signals, not legal conclusions.
5. You acknowledge the free-tier service limitations (rate limits, storage quotas).

**Prohibited uses:**

- Submitting fabricated evidence
- Attempting to manipulate LLM outputs
- Bulk scraping of the API without permission
- Using VERA output in legal proceedings without independent expert verification

---

*For questions: [privacy@vera-platform.example]*  
*Grievance officer (DPDP Act §13(6)): [grievance@vera-platform.example]*

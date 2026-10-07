# VERA Security Policy

## Reporting Security Issues

We take the security of the VERA Investment-Fraud Investigation Platform seriously. If you discover a vulnerability or security flaw, please report it privately:

- **Email:** `security@vera-platform.org` (or contact project leads via PGP)
- **Do not open public GitHub issues for security vulnerabilities.**

---

## Architecture Security Rules & Invariants

### 1. Secret Protection (Architecture Rule 11)
- **Zero Committed Secrets:** Under no circumstance may private API keys, database credentials, service role tokens, or signing keys be committed to Git.
- All environment configurations must reference `.env.example`.
- CI runs automated secret detection (`git ls-files` check) preventing commits of `.env` files.

### 2. Zero-Trust Evidence Isolation
- Unverified APK binaries, suspicious PDFs, and downloaded media files are treated as untrusted and hostile payloads.
- Forensic decompilation (Androguard/JADX) and media parsing (FFmpeg/OpenCV) must execute within isolated container runtimes with restricted system privileges.

### 3. Failsafe Scoring Integrity (Architecture Rule 6, 7 & 9)
- LLMs are sandboxed from the final scoring pipeline. Prompt injection into LLM prompts cannot alter the deterministic mathematical calculation.
- Analyzer failures result in elevated uncertainty penalties, preventing adversarial evasion via crash induction.

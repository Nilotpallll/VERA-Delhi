# VERA Phase 5 Implementation Plan: LangGraph Investigator & Deterministic Correlation

This document specifies the architecture, state machine, tool contracts, deterministic risk engine, and evaluation benchmarks for Phase 5 of VERA (LangGraph Investigator).

---

## 1. Objectives & Architectural Principles

Phase 5 implements the unified **VERA Investigator Agent** orchestrated via **LangGraph**, binding the specialized detection engines (Phase 4), the regulatory knowledge pipeline (Phase 3), and canonical relational storage (Phase 2) into a cohesive agentic loop.

### Core Principles
* **One Investigator:** A single stateful LangGraph agent driving the investigation lifecycle.
* **Many Tools:** 13 modular, failsafe tool interfaces for multimodal analysis, entity verification, and intelligence retrieval.
* **One Evidence Format:** Strict conformance to `CanonicalEvidenceItem` (`EvidenceItem`).
* **One Risk Engine:** 100% deterministic, rule-weighted mathematical risk attribution.
* **One Report:** Unified, auditable, court-ready forensic report.

### Strict Agent Invariants (Rules 6, 7, 8, 9, 13)
* **Mathematical Determinism:** LLMs and agent steps may NEVER assign numerical risk scores directly.
* **Tri-State Verification:** Every verification tool must emit `VERIFIED`, `NOT_VERIFIED`, or `UNAVAILABLE`.
* **Zero-Trust Failsafe:** Analyzer failures and timeouts incur uncertainty penalties and yield `PARTIAL` or `INSUFFICIENT_EVIDENCE`.
* **Append-Only Evidence:** Evidence items cannot be overwritten or deleted.
* **Zero Chain-of-Thought Exposure:** Internal agent reasoning is sequestered from final reports.
* **Source Citation Invariant:** No regulatory match or claim may be reported without authentic citations.

---

## 2. Agent Loop State Machine (LangGraph)

```
[INPUT]
   │
   ▼
[understand_input]
   │
   ▼
[extract_claims_entities]
   │
   ▼
[decide_investigation_actions] ◄──────────────────┐
   │                                              │ (need more evidence
   ▼                                              │  and iteration < max)
[execute_tools]                                   │
   │                                              │
   ▼                                              │
[correlate_evidence]                              │
   │                                              │
   ▼                                              │
[determine_missing_evidence] ─────────────────────┘
   │
   │ (sufficient OR max_iterations reached)
   ▼
[risk_engine_node]
   │
   ▼
[generate_report_node]
   │
   ▼
 [END]
```

---

## 3. Tool Interfaces (13 Specialized Tools)

1. `analyze_message`: Text entity/claim extraction, urgency, solicitation heuristics.
2. `analyze_image`: OCR text extraction, ELA tampering markers, layout analysis.
3. `analyze_video`: Frame extraction, face tracking, MesoNet deepfake inference.
4. `transcribe_audio`: Speech-to-text transcript, acoustic artifact checks.
5. `analyze_url`: Lexical features, domain age, DNS/TLS checks, XGBoost classification.
6. `analyze_apk`: Manifest inspection, dangerous permissions, certificates, Drebin features.
7. `verify_sebi_entity`: Authoritative regulatory intermediary lookup (tri-state).
8. `verify_company`: MCA/ROC entity registration audit (tri-state).
9. `verify_domain`: WHOIS / brand typosquatting similarity check (tri-state).
10. `verify_payment`: UPI handle and banking credential mismatch verification.
11. `retrieve_guidance`: BGE-M3 semantic retrieval over official SEBI circulars with citations.
12. `search_authoritative_source`: Direct querying of official gazettes and advisory alerts.
13. `lookup_indicator`: Query known malicious indicators (phone, domain, UPI, APK SHA256).

---

## 4. Deterministic Risk Engine Specification

### Heuristic Signals & Weights
* `guaranteed_return`: +15 (Assured profit, zero-risk claims)
* `unverified_entity`: +25 (Claimed regulatory credential not found in registry)
* `domain_mismatch`: +20 (Typosquatted domain, brand impersonation)
* `payment_mismatch`: +20 (Direct payment to third-party or individual UPI for corporate advice)
* `withdrawal_fee`: +20 (Demanding fee/tax before releasing capital)
* `known_indicator`: +25 (Matches known scam blacklist / alert list)
* `suspicious_apk`: +25 (Overlay permissions, SMS interception, debug cert)
* `deepfake_signal`: +25 (Facial manipulation signal or cloned audio)

### Scoring Constraints
* Raw scores are summed and capped strictly at **100**.
* **Risk Bands:**
  * `0 – 24`: `LOW`
  * `25 – 49`: `MODERATE`
  * `50 – 74`: `HIGH`
  * `75 – 100`: `CRITICAL`
* **Mandatory Notice:** `"These risk scores are prototype heuristic weights, NOT probabilities of fraud."`
* **Separation of Dimensions:**
  * `model_confidence` (0.0 to 1.0)
  * `verification_status` (`VERIFIED` | `NOT_VERIFIED` | `UNAVAILABLE`)
  * `risk_score` (0.0 to 100.0)
  * `investigation_completeness` (`COMPLETED` | `PARTIAL` | `INSUFFICIENT_EVIDENCE`)

---

## 5. End-to-End Evaluation Scenarios

1. **Benign Investment Message:** Official AMC advisory, verified entity, low risk.
2. **Guaranteed-Return Scam:** WhatsApp message promising 100% guaranteed 3X profit in 7 days.
3. **Fake SEBI Representative:** Individual claiming SEBI officer status with spoofed number.
4. **Fake Trading Website:** Typosquatted portal collecting credentials.
5. **Suspicious APK:** Trading app binary with SMS reading & overlay permissions.
6. **Manipulated Investment Video:** Celebrity endorsement with MesoNet deepfake signal.
7. **Mixed-Evidence Case:** Telegram group invite + counterfeit registration cert + personal UPI.
8. **Insufficient Evidence Case:** Ambiguous one-liner with no verifiable indicators.

---

## 6. Phase Gate Acceptance Criteria
* Risk score is 100% reproducible from stored evidence and ruleset version.
* Agent respects maximum tool call limit and cyclic loop guards.
* Prompt injections fail to manipulate risk score or bypass verification gates.
* All 193 existing tests remain passing + complete Phase 5 test coverage.

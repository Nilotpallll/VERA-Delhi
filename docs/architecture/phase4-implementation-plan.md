# VERA Phase 4 Implementation Plan: Specialized Detection Modules

This document specifies the architecture, engine interfaces, data contracts, and verification gates for Phase 4 of VERA (Specialized Detection Modules).

---

## 1. Objectives & Architectural Boundaries

Phase 4 implements independent, specialized forensic and heuristic detection analyzers across all digital evidence modalities, adhering strictly to:
* **Architecture Rule 4**: Detection engines are independent modules.
* **Architecture Rule 5**: Evidence uses one canonical schema.
* **Architecture Rule 6 & 7**: Risk scoring is 100% deterministic; no detector may directly modify the risk score.
* **Architecture Rule 8**: Verification states must be tri-state (`VERIFIED`, `NOT_VERIFIED`, `UNAVAILABLE`).
* **Architecture Rule 9**: Analyzer failure must never be interpreted as safety (`uncertainty=1.0`, mark investigation `PARTIAL`).
* **Architecture Rule 12**: Every model/analyzer exposes version metadata (semver + weights/rules digest).
* **Architecture Rule 13**: Every investigation is reproducible.
* **Architecture Rule 15**: Zero paid dependencies, free-tier/local-first compatible.

---

## 2. Detection Module Specifications

### 2.1 Message Detection Engine (`MessageAnalyzer`)
* **Entity Extraction**: Phone numbers, emails, UPI IDs, URLs, company/brand names, person names.
* **Claim Extraction**: Promised return percentages, guaranteed timeframes, registration claims.
* **Urgency Detection**: "urgent", "immediately", "hurry", "last chance", "limited slots", "act fast".
* **Guaranteed-Return Detection**: "100% guaranteed", "assured profit", "zero risk", "capital protection".
* **Impersonation Indicators**: Misuse of SEBI, NSE, BSE, RBI, reputable AMC/broker brands.
* **Withdrawal-Fee Indicators**: Advance tax deposit, release fee, unfreeze commission, processing penalty.
* **Investment Solicitation Indicators**: Unauthorized signal groups, deposit requests, VIP trading invites.

### 2.2 Image Detection Engine (`ImageAnalyzer`)
* **OCR**: Integrated text extraction with confidence and polygon bounding box metadata.
* **Image Metadata Extraction**: Format, dimensions, aspect ratio, color mode, EXIF software/editor tags (Photoshop/Canva tampering markers).
* **Manipulation Indicators**: Error Level Analysis (ELA) compression discrepancy, copy-move clone artifact indicators, noise variance anomalies.
* **Screenshot Structure Analysis**: Fake trading app layout misalignment, font discrepancies, spoofed status bars, altered timestamps.

### 2.3 Video Deepfake Detection Engine (`VideoAnalyzer`)
* **FFmpeg / OpenCV Frame Extraction**: Frame sampling at uniform intervals across video duration.
* **Face Detection**: Multi-frame facial landmark and bounding box tracking.
* **MesoNet Inference**: Meso-4 deepfake facial manipulation analysis.
* **Temporal Aggregation**: Per-frame variance, temporal flickering anomaly metrics.
* **Mandatory Phrasing Rule**:
  * Allowed: `"Model detected signals associated with facial manipulation."`
  * Strictly Prohibited: `"This video is definitely fake."`

### 2.4 Audio Detection Engine (`AudioAnalyzer`)
* **Audio Extraction**: Container demuxing into standardized audio streams.
* **Faster-Whisper Integration**: Transcript generation with word/segment level confidence.
* **Transcript Analysis**: Urgency, guaranteed profit, voice cloning / TTS acoustic artifact indicators.

### 2.5 URL Detection Engine (`URLAnalyzer`)
* **Deterministic Analysis**:
  * Lexical features: Length, entropy, special chars, hyphen/subdomain density.
  * Domain & Punycode: IDN homograph detection, age/expiry heuristics.
  * DNS & TLS: Resolution check, certificate validity, self-signed detection.
  * Redirects: Hop count, circular redirect detection, protocol downgrade.
  * Security Indicators: IP-host address detection, suspicious TLD list (`.xyz`, `.top`, `.work`, `.loan`, etc.).
  * Brand Similarity: Levenshtein distance against major Indian financial institutions.
  * HTML Analysis: Hidden forms, external credential post destinations, iframe phishing overlays.
* **XGBoost URL Classifier**: Gradient-boosted feature vector inference with exposed model version.

### 2.6 APK Static Analysis Engine (`APKAnalyzer`)
* **Static Analysis**:
  * Cryptographic SHA256 digest computation.
  * Manifest parsing: Package name, activities, services, receivers.
  * Dangerous Permissions: `RECEIVE_SMS`, `READ_SMS`, `SYSTEM_ALERT_WINDOW`, `REQUEST_INSTALL_PACKAGES`, `BIND_ACCESSIBILITY_SERVICE`.
  * Certificates: Debug certificate detection (`CN=Android Debug`), self-signed flags.
  * API Calls & Dex Strings: Reflection (`Class.forName`), dynamic loading (`DexClassLoader`), C2 endpoints.
  * Suspicious Components: Overlay injection patterns, dropper architectures.
* **Drebin Feature Extraction & XGBoost**: Drebin 8-set feature mapping (S1–S8) with XGBoost static risk classification.
* **Sandbox Policy**: No dynamic execution sandbox (strictly static analysis).

### 2.7 Profile Analysis Engine (`ProfileAnalyzer`)
* **Scope**: Publicly supplied profile URLs only (Twitter/X, Telegram, Instagram, LinkedIn, YouTube, Facebook).
* **Extracted Fields**: Username, display name, bio, public links, claimed organization, public contact information.
* **Privacy Boundary**: Zero authentication bypass, zero private credential scraping.

---

## 3. Common Evidence & Failsafe Architecture

Every analyzer:
1. Subclasses `BaseAnalyzer` and implements `metadata` and `_execute(evidence)`.
2. Normalizes outputs to `CanonicalEvidenceItem`.
3. Handles exceptions via the safe execution harness:
   * Sets status to `FAILED`.
   * Sets `uncertainty = 1.0`.
   * Flags `has_analyzer_failure = True`.
   * Sets investigation status to `PARTIAL`.
   * Never lowers risk score or fabricates results.
4. Strictly adheres to Phase Gate:
   * No detector directly modifies the risk score.
   * All signals flow through the canonical evidence layer into the deterministic scoring engine.

---

## 4. ML Evaluation Reporting

URL, APK, and deepfake models implement `ModelEvaluationReporter` computing:
* Precision
* Recall
* F1 Score
* Confusion Matrix (`[[TN, FP], [FN, TP]]`)
* False-Negative Rate (FNR)
* Mean & P95 Latency (ms)
* Inference Failure Rate
* Model Version Attribution

# VERA Phase 3 Implementation Plan: Language & Knowledge Intelligence

This document details the architecture, design, and roadmap for Phase 3 of VERA (Language & Knowledge Intelligence).

---

## 1. Objectives & Boundaries

### Permitted LLM Tasks:
1. **Extract entities** (`PERSON`, `COMPANY`, `PHONE`, `EMAIL`, `UPI`, `DOMAIN`, `URL`, `PROFILE`, `APK`, `MESSAGE`, `IMAGE`, `VIDEO`, `AUDIO`)
2. **Extract claims** (with claim type, source reference, confidence)
3. **Identify linguistic risk indicators** (urgency, FOMO, guaranteed returns, pressure tactics, secrecy)
4. **Classify scam stage** (hook, groom, trust_building, investment_ask, fake_profit_display, withdrawal_block, exit)
5. **Interpret evidence** (explaining relationship between evidence items)
6. **Plan investigations** (suggesting recommended next analyzers or checks)
7. **Summarize evidence** (executive summaries based strictly on verified inputs)
8. **Generate reports** (narrative drafting)

### Strict LLM Prohibitions:
- **MUST NOT determine final risk score** (Architecture Rule 6, 7 — scoring is 100% deterministic)
- **MUST NOT claim official verification without evidence** (Rule 8)
- **MUST NOT invent sources**
- **MUST NOT fabricate SEBI rules or circulars**
- **MUST NOT declare a person a fraudster from weak/unverified evidence**

---

## 2. Component Architecture

```
apps/api/src/
├── ai/
│   ├── base.py                   # LLMProvider, EmbeddingProvider, LLMGenerationResult
│   ├── factory.py                # Configuration-based provider resolver (Gemini / Ollama / Groq)
│   ├── gemini.py                 # Gemini Free-Tier provider
│   ├── ollama.py                 # Ollama local open-weights provider
│   ├── groq.py                   # Groq free-tier provider
│   ├── bge_m3.py                 # BGE-M3 embedding provider (1024-d, local fallback)
│   └── tasks/
│       ├── __init__.py
│       ├── entity_extraction.py  # LLM entity extraction task
│       ├── claim_extraction.py   # LLM claim extraction task
│       ├── linguistic_risk.py    # Linguistic risk indicators
│       ├── scam_stage.py         # Scam stage classification
│       ├── evidence_summary.py   # Evidence summarizer
│       └── report_narrative.py   # Narrative drafting
├── engines/
│   ├── ocr_engine.py             # PaddleOCR engine adapter & evidence normalizer
│   └── stt_engine.py             # faster-whisper engine adapter & evidence normalizer
├── knowledge/
│   ├── __init__.py
│   ├── fetcher.py                # Official-source fetcher (SEBI/RBI/NSE/BSE/MCA)
│   ├── parser.py                 # Document parser, cleaner, chunker, metadata extractor
│   ├── store.py                  # pgvector & in-memory vector storage
│   ├── retriever.py              # Semantic retrieval + Citation generation
│   ├── guideline_matcher.py      # SEBI guideline matching with strict citations
│   └── evaluation.py             # Labeled benchmark set & evaluation metrics
└── models/
    └── knowledge.py              # KnowledgeDocument & KnowledgeChunk ORM models
```

---

## 3. SEBI Knowledge Pipeline Specification

### Ingestion Flow:
1. `OfficialSourceFetcher`: Fetches circulars, regulations, alerts, advisory notices.
2. `DocumentParser & Cleaner`: Strips boilerplate, extracts publication dates, titles, reference numbers.
3. `Chunker`: Chunks into semantic segments (~300–500 tokens) with overlap.
4. `MetadataExtractor`: Enriches chunks with `source_url`, `title`, `publisher`, `publication_date`, `retrieval_date`, `document_hash`, `license_info`, `version`.
5. `BGE-M3 Embedder`: Computes 1024-dimensional dense vectors.
6. `Storage & Retrieval`: Stored in pgvector (`knowledge_documents`, `knowledge_chunks`), retrieved by cosine similarity.
7. `Citation Generation`: Every retrieved guideline returns structured citation object.

### Failsafe Invariant:
- If retrieval yields no confident matches (similarity < threshold): return `KNOWLEDGE_UNAVAILABLE`.
- If an official source cannot be verified against official registry: return `VERIFICATION_UNAVAILABLE`.
- Unsupported SEBI claims never reach a final report.

---

## 4. Evaluation Benchmark Metrics
- **Dataset**: Genuine investment guidance, scam messages, guaranteed-return claims, impersonation, registration claims, ambiguous claims, adversarial prompts.
- **Metrics**: Precision, Recall, F1, Citation Accuracy, False-Positive Rate (FPR), False-Negative Rate (FNR).

---

## 5. Execution Steps
- **Step 1**: Implement LLM Task modules (`apps/api/src/ai/tasks/`) with JSON schema enforcement, injection defense, and failsafes.
- **Step 2**: Implement OCR Normalizer (`apps/api/src/engines/ocr_engine.py`) and STT Normalizer (`apps/api/src/engines/stt_engine.py`).
- **Step 3**: Implement SEBI Knowledge Pipeline (`apps/api/src/knowledge/`).
- **Step 4**: Implement Guideline Matcher with citation enforcement.
- **Step 5**: Create evaluation benchmark set & metrics calculator.
- **Step 6**: Create comprehensive test suite (LLM, OCR, STT, RAG, Eval set) and verify Phase Gate.

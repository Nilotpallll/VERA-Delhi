# ADR-003: LLM Provider Abstraction and Deterministic Risk Scoring

## Status
Accepted

## Context
Generative AI models are non-deterministic, prone to hallucination, and vulnerable to prompt injection. Allowing an LLM to directly assign a numerical fraud risk score (e.g. "Risk: 87/100") violates evidentiary integrity and MNC compliance standards. Furthermore, vendor lock-in to proprietary models creates cost and availability risks.

## Decision
1. **Rule 3 (Provider Abstraction):** All LLM interactions occur through the `LLMProvider` interface. Supported providers include:
   - Google Gemini 1.5 Flash (free tier)
   - Ollama (local Llama 3.2 on-premises)
   - Groq (optional fast free tier)
2. **Rule 6 & 7 (Deterministic Scoring Invariant):**
   - LLMs are strictly restricted to entity extraction, OCR transcription cleaning, and structured fact synthesis.
   - **LLMs cannot directly assign final risk scores.**
   - Final risk scores are calculated by `DeterministicScoringEngine` using mathematical weighted aggregations:
     $$\text{Final Score} = \frac{\sum (w_i \cdot s_i)}{\sum w_i} + \text{Uncertainty Penalty}$$
   - The contract enforces `is_llm_assigned: false` as an immutable assertion.

## Consequences
- Repeated execution over identical evidence guarantees byte-for-byte identical risk scores.
- Zero paid API dependencies required; local fallback supported out of the box.
- Audit trails can trace every score point directly to deterministic rule IDs.

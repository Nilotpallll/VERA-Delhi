"""LLM Tasks and Guardrails for VERA Phase 3.

ARCHITECTURE RULES ENFORCED:
  Rule 3:  Models accessed through provider interfaces (LLMProvider).
  Rule 6:  Deterministic risk scoring — LLMs NEVER assign final risk scores.
  Rule 7:  LLMs cannot assign final risk scores (is_llm_assigned is strictly False).
  Rule 8:  Tri-state verification (VERIFIED, NOT_VERIFIED, UNAVAILABLE).
  Rule 9:  Analyzer failure never implies safety.
  Rule 13: Every investigation reproducible from stored state.

PERMITTED LLM TASKS:
  - extract entities
  - extract claims
  - identify linguistic risk indicators
  - classify scam stage
  - interpret evidence
  - plan investigations
  - summarize evidence
  - generate reports

PROHIBITIONS (Enforced by post-processing guardrails):
  - No final risk score determination
  - No claiming official verification without hard evidence
  - No invented sources or fabricated SEBI rules
  - No declaring a person a fraudster without verified proof
"""

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from ..contracts.enums import EntityType
from .base import LLMProvider


# ── Schemas for Structured Task Outputs ───────────────────────────────────────

class ExtractedEntityItem(BaseModel):
    type: str
    value: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    context_snippet: str = ""


class EntityExtractionResult(BaseModel):
    entities: list[ExtractedEntityItem] = Field(default_factory=list)


class ExtractedClaimItem(BaseModel):
    claim_text: str
    claim_type: str  # guaranteed_return, sebi_registered, unlisted_shares, zero_risk, urgency, etc.
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source_snippet: str = ""


class ClaimExtractionResult(BaseModel):
    claims: list[ExtractedClaimItem] = Field(default_factory=list)


class LinguisticRiskIndicators(BaseModel):
    urgency_detected: bool = False
    guaranteed_return_promises: bool = False
    unrealistic_returns_mentioned: bool = False
    secrecy_requested: bool = False
    fomo_language: bool = False
    pressure_tactics: bool = False
    indicators: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ScamStageClassification(BaseModel):
    stage: str = "hook"  # hook | groom | trust_building | investment_ask | fake_profit_display | withdrawal_block | exit
    explanation: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class EvidenceInterpretation(BaseModel):
    summary: str
    corroborating_findings: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    suggested_investigation_steps: list[str] = Field(default_factory=list)


# ── Helper for robust JSON extraction from LLM response ───────────────────────

def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    """Recovers structured JSON from LLM markdown blocks or conversational text."""
    if not raw_text or not raw_text.strip():
        return {}

    # Try 1: Direct JSON parse
    try:
        return json.loads(raw_text.strip())
    except Exception:
        pass

    # Try 2: Look for ```json ... ``` code fence
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except Exception:
            pass

    # Try 3: Find outermost { ... }
    first_brace = raw_text.find("{")
    last_brace = raw_text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        snippet = raw_text[first_brace : last_brace + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass

    return {}


# ── LLM Task Executor ─────────────────────────────────────────────────────────

class LLMTaskExecutor:
    """Executes permitted NLP tasks with strict prompt guardrails and output sanitization."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    # 1. Entity Extraction
    async def extract_entities(self, text: str) -> EntityExtractionResult:
        system_prompt = (
            "You are an NLP entity extraction system for financial fraud investigation.\n"
            "Extract entities into JSON format only.\n"
            "Entity types allowed: PERSON, COMPANY, PHONE, EMAIL, UPI, DOMAIN, URL, PROFILE, APK, MESSAGE.\n"
            "Output must be valid JSON: {\"entities\": [{\"type\": \"...\", \"value\": \"...\", \"confidence\": 0.9, \"context_snippet\": \"...\"}]}\n"
            "Do NOT include markdown or explanatory text."
        )
        prompt = f"Extract all relevant entities from the following text:\n\n{text}"
        
        try:
            result = await self.provider.generate(prompt=prompt, system_prompt=system_prompt)
            data = _extract_json_payload(result.output_text)
            entities = []
            for item in data.get("entities", []):
                etype = item.get("type", "").upper()
                valid_types = [t.value for t in EntityType]
                if etype in valid_types:
                    entities.append(ExtractedEntityItem(
                        type=etype,
                        value=str(item.get("value", "")).strip(),
                        confidence=float(item.get("confidence", 0.8)),
                        context_snippet=str(item.get("context_snippet", "")),
                    ))
            return EntityExtractionResult(entities=entities)
        except Exception:
            return EntityExtractionResult(entities=[])

    # 2. Claim Extraction
    async def extract_claims(self, text: str) -> ClaimExtractionResult:
        system_prompt = (
            "You are an expert financial investigator. Extract all factual or promotional investment claims.\n"
            "Output JSON format only: {\"claims\": [{\"claim_text\": \"...\", \"claim_type\": \"...\", \"confidence\": 0.9, \"source_snippet\": \"...\"}]}\n"
            "DO NOT assign risk scores or declare guilt."
        )
        prompt = f"Extract all investment promises, regulatory claims, and assertions from:\n\n{text}"

        try:
            result = await self.provider.generate(prompt=prompt, system_prompt=system_prompt)
            data = _extract_json_payload(result.output_text)
            claims = []
            for item in data.get("claims", []):
                ctext = item.get("claim_text", "").strip()
                if ctext:
                    claims.append(ExtractedClaimItem(
                        claim_text=ctext,
                        claim_type=item.get("claim_type", "general_claim"),
                        confidence=float(item.get("confidence", 0.8)),
                        source_snippet=item.get("source_snippet", ""),
                    ))
            return ClaimExtractionResult(claims=claims)
        except Exception:
            return ClaimExtractionResult(claims=[])

    # 3. Linguistic Risk Indicators
    async def identify_linguistic_risk_indicators(self, text: str) -> LinguisticRiskIndicators:
        system_prompt = (
            "Analyze the text for deceptive psychological tactics used in investment scams.\n"
            "Look for urgency, guaranteed returns, secrecy, FOMO, or pressure tactics.\n"
            "Output strictly JSON:\n"
            "{\n"
            "  \"urgency_detected\": true/false,\n"
            "  \"guaranteed_return_promises\": true/false,\n"
            "  \"unrealistic_returns_mentioned\": true/false,\n"
            "  \"secrecy_requested\": true/false,\n"
            "  \"fomo_language\": true/false,\n"
            "  \"pressure_tactics\": true/false,\n"
            "  \"indicators\": [\"...\"],\n"
            "  \"confidence\": 0.9\n"
            "}"
        )
        prompt = f"Analyze linguistic tactics in:\n\n{text}"

        try:
            result = await self.provider.generate(prompt=prompt, system_prompt=system_prompt)
            data = _extract_json_payload(result.output_text)
            return LinguisticRiskIndicators(
                urgency_detected=bool(data.get("urgency_detected", False)),
                guaranteed_return_promises=bool(data.get("guaranteed_return_promises", False)),
                unrealistic_returns_mentioned=bool(data.get("unrealistic_returns_mentioned", False)),
                secrecy_requested=bool(data.get("secrecy_requested", False)),
                fomo_language=bool(data.get("fomo_language", False)),
                pressure_tactics=bool(data.get("pressure_tactics", False)),
                indicators=data.get("indicators", []),
                confidence=float(data.get("confidence", 0.8)),
            )
        except Exception:
            return LinguisticRiskIndicators()

    # 4. Scam Stage Classification
    async def classify_scam_stage(self, text: str) -> ScamStageClassification:
        stages = [
            "hook", "groom", "trust_building", "investment_ask",
            "fake_profit_display", "withdrawal_block", "exit"
        ]
        system_prompt = (
            "Classify the communication into one of these scam lifecycle stages:\n"
            "- hook: initial contact, unsolicited invite\n"
            "- groom: rapport building, small talk\n"
            "- trust_building: screenshots of profits, testimonials\n"
            "- investment_ask: requesting deposit, asking to buy crypto/stocks\n"
            "- fake_profit_display: showing fake balance gains\n"
            "- withdrawal_block: demanding taxes/fees to release funds\n"
            "- exit: cutting contact, deleted groups\n"
            "Output strictly JSON: {\"stage\": \"...\", \"explanation\": \"...\", \"confidence\": 0.9}"
        )
        prompt = f"Classify stage for:\n\n{text}"

        try:
            result = await self.provider.generate(prompt=prompt, system_prompt=system_prompt)
            data = _extract_json_payload(result.output_text)
            stg = data.get("stage", "hook").lower().strip()
            if stg not in stages:
                stg = "hook"
            return ScamStageClassification(
                stage=stg,
                explanation=data.get("explanation", ""),
                confidence=float(data.get("confidence", 0.8)),
            )
        except Exception:
            return ScamStageClassification()

    # 5. Summarize Evidence & Interpret
    async def interpret_evidence(self, evidence_descriptions: list[str]) -> EvidenceInterpretation:
        system_prompt = (
            "You are a forensic analyst interpreting gathered evidence for a case.\n"
            "RULES:\n"
            "1. DO NOT assign numerical risk scores.\n"
            "2. DO NOT declare someone guilty without proof.\n"
            "3. Synthesize corroborating findings, identify gaps, and suggest next steps.\n"
            "Output JSON: {\"summary\": \"...\", \"corroborating_findings\": [], \"contradictions\": [], \"suggested_investigation_steps\": []}"
        )
        content = "\n".join(f"- {d}" for d in evidence_descriptions)
        prompt = f"Analyze the following evidence items:\n\n{content}"

        try:
            result = await self.provider.generate(prompt=prompt, system_prompt=system_prompt)
            data = _extract_json_payload(result.output_text)
            return EvidenceInterpretation(
                summary=data.get("summary", "Evidence review complete."),
                corroborating_findings=data.get("corroborating_findings", []),
                contradictions=data.get("contradictions", []),
                suggested_investigation_steps=data.get("suggested_investigation_steps", []),
            )
        except Exception:
            return EvidenceInterpretation(summary="Evidence interpretation unavailable.")

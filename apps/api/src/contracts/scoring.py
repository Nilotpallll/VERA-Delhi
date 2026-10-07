"""Deterministic Risk Scoring Contracts.

Architecture Rule 6: Risk scoring is deterministic.
Architecture Rule 7: LLMs cannot directly assign final risk scores.
Architecture Rule 9: Analyzer failure must never be interpreted as safety.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RiskSeverityTier(StrEnum):
    CRITICAL = "CRITICAL"  # 80 - 100
    HIGH = "HIGH"          # 60 - 79
    MEDIUM = "MEDIUM"      # 40 - 59
    LOW = "LOW"            # 10 - 39
    SAFE = "SAFE"          # 0 - 9
    INCONCLUSIVE = "INCONCLUSIVE"


class ScoreFactorContribution(BaseModel):
    factor_id: str
    name: str
    category: Literal[
        "registry_check",
        "media_authenticity",
        "claims_analysis",
        "apk_heuristics",
        "uncertainty_penalty"
    ]
    weight: float = Field(ge=0.0, le=1.0)
    raw_score: float = Field(ge=0.0, le=100.0)
    weighted_score: float = Field(ge=0.0, le=100.0)
    reason: str
    deterministic_rule_id: str


class DeterministicRiskAssessment(BaseModel):
    final_score: float = Field(..., ge=0.0, le=100.0, description="Mathematical score strictly 0-100")
    tier: RiskSeverityTier
    factors: list[ScoreFactorContribution]
    uncertainty_penalty: float = Field(default=0.0, ge=0.0, le=100.0)
    algorithm_version: str = "scoring.v1.0"
    summary: str
    # Architectural assertion: LLM cannot assign the final score
    is_llm_assigned: Literal[False] = False

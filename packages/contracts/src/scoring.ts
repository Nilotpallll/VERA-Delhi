/**
 * Deterministic Risk Scoring Contracts.
 * Architecture Rule 6: Risk scoring is deterministic.
 * Architecture Rule 7: LLMs cannot directly assign final risk scores.
 * Architecture Rule 9: Analyzer failure must never be interpreted as safety.
 */

export enum RiskSeverityTier {
  CRITICAL = "CRITICAL", // 80 - 100
  HIGH = "HIGH",         // 60 - 79
  MEDIUM = "MEDIUM",     // 40 - 59
  LOW = "LOW",           // 10 - 39
  SAFE = "SAFE",         // 0 - 9
  INCONCLUSIVE = "INCONCLUSIVE" // Analyzer failed or missing critical verification
}

export interface ScoreFactorContribution {
  factorId: string;
  name: string;
  category: "registry_check" | "media_authenticity" | "claims_analysis" | "apk_heuristics" | "uncertainty_penalty";
  weight: number;          // Relative weight (0.0 to 1.0)
  rawScore: number;        // Raw factor score (0 to 100)
  weightedScore: number;   // weight * rawScore
  reason: string;
  deterministicRuleId: string;
}

export interface DeterministicRiskAssessment {
  /** Overall computed score strictly from 0 to 100 */
  finalScore: number;
  /** Categorized severity tier */
  tier: RiskSeverityTier;
  /** Mathematical breakdown of all factors contributing to the final score */
  factors: ScoreFactorContribution[];
  /** Penalty applied when analyzers fail or evidence is UNAVAILABLE */
  uncertaintyPenalty: number;
  /** Deterministic algorithm version code, e.g. "scoring.v1.0" */
  algorithmVersion: string;
  /** Explanation generated from deterministic rule traces */
  summary: string;
  /** Explicit architectural assertion: LLM cannot override this score directly */
  isLlmAssigned: false;
}

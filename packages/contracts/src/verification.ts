/**
 * Verification state contracts for VERA fraud investigation platform.
 * Architecture Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED, and UNAVAILABLE.
 * Architecture Rule 9: Analyzer failure must never be interpreted as safety.
 */

export enum VerificationState {
  /** Positively confirmed against authoritative registries or ground-truth evidence */
  VERIFIED = "VERIFIED",
  /** Examined but cannot be corroborated, contradicts evidence, or is falsified */
  NOT_VERIFIED = "NOT_VERIFIED",
  /** System was unable to verify (registry down, rate-limited, timeout, unparseable) */
  UNAVAILABLE = "UNAVAILABLE"
}

export enum AnalyzerExecutionStatus {
  SUCCESS = "SUCCESS",
  FAILED = "FAILED",
  TIMED_OUT = "TIMED_OUT",
  SKIPPED = "SKIPPED"
}

export interface VerificationResult {
  state: VerificationState;
  source: string;
  verifiedAt: string;
  confidence: number; // 0.0 to 1.0
  details: string;
  rawResponseHash?: string;
  /** Set to true when an analyzer encountered failure; downstream rules must treat as elevated uncertainty */
  hasAnalyzerFailure: boolean;
}

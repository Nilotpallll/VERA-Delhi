/**
 * Analyzer and Model contract definitions.
 * Architecture Rule 4: Detection engines are independent modules.
 * Architecture Rule 12: Every model/analyzer must expose version metadata.
 */

import { AnalyzerExecutionStatus } from "./verification";

export interface AnalyzerMetadata {
  /** Unique engine identifier, e.g. "engine.ocr.paddle", "engine.deepfake.mesonet" */
  name: string;
  /** Semantic version of analyzer logic */
  version: string;
  /** Cryptographic hash or identifier of model weights/ruleset */
  weightsOrConfigDigest: string;
  /** Author / Maintainer */
  provider: string;
}

export interface AnalyzerExecutionRecord {
  metadata: AnalyzerMetadata;
  status: AnalyzerExecutionStatus;
  startedAt: string;
  completedAt: string;
  executionDurationMs: number;
  /** If status is FAILED or TIMED_OUT, details must describe failure */
  errorMessage?: string;
  /** Arbitrary structured findings produced by this engine */
  findings: Record<string, unknown>;
  /** Uncertainty metric between 0.0 (certain) and 1.0 (completely uncertain) */
  uncertainty: number;
}

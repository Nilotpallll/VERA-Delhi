import test from "node:test";
import assert from "node:assert/strict";
import {
  VERA_API_VERSION,
  VERA_API_PREFIX,
  VerificationState,
  AnalyzerExecutionStatus,
  RiskSeverityTier,
  EvidenceMediaType,
  InvestigationStatus
} from "../dist/index.js";

test("VERA contracts verification and API version integrity", () => {
  assert.equal(VERA_API_VERSION, "v1");
  assert.equal(VERA_API_PREFIX, "/api/v1");

  // Rule 8: Verification must distinguish VERIFIED, NOT_VERIFIED, and UNAVAILABLE
  assert.equal(VerificationState.VERIFIED, "VERIFIED");
  assert.equal(VerificationState.NOT_VERIFIED, "NOT_VERIFIED");
  assert.equal(VerificationState.UNAVAILABLE, "UNAVAILABLE");

  // Rule 9: Analyzer failure must be explicitly represented
  assert.equal(AnalyzerExecutionStatus.FAILED, "FAILED");

  // Severity tiers & Evidence Media types
  assert.equal(RiskSeverityTier.CRITICAL, "CRITICAL");
  assert.equal(EvidenceMediaType.APK, "APK");
  assert.equal(InvestigationStatus.COMPLETED, "COMPLETED");
});

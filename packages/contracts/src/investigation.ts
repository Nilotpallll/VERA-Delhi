/**
 * Investigation API contracts.
 * Architecture Rule 1: Frontend communicates only through API contracts.
 * Architecture Rule 2: API contracts are versioned.
 * Architecture Rule 13: Every investigation must be reproducible from stored versions/configuration.
 */

import { CanonicalEvidenceItem, EvidenceMediaType } from "./evidence";
import { DeterministicRiskAssessment } from "./scoring";
import { AnalyzerExecutionRecord } from "./analyzers";

export enum InvestigationStatus {
  PENDING = "PENDING",
  PROCESSING = "PROCESSING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED"
}

export interface InvestigationCreateRequest {
  title: string;
  targetEntityName?: string;
  primaryUrl?: string;
  summaryNote?: string;
  initialEvidenceItems?: Array<{
    mediaType: EvidenceMediaType;
    contentPayload?: string;
    sourceOrigin: string;
    tags?: string[];
  }>;
}

export interface InvestigationManifest {
  investigationId: string;
  createdAt: string;
  engineSemver: string;
  scoringAlgorithmVersion: string;
  analyzerVersions: Record<string, string>;
  configurationDigest: string;
  inputDigest: string;
}

export interface InvestigationResponse {
  id: string;
  status: InvestigationStatus;
  title: string;
  targetEntityName?: string;
  primaryUrl?: string;
  evidenceCount: number;
  evidence: CanonicalEvidenceItem[];
  riskAssessment?: DeterministicRiskAssessment;
  analyzerRecords: AnalyzerExecutionRecord[];
  manifest: InvestigationManifest;
  createdAt: string;
  updatedAt: string;
}

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  apiVersion: string;
  timestamp: string;
  components: {
    database: "connected" | "disconnected" | "unconfigured";
    redis: "connected" | "disconnected" | "unconfigured";
    storage: "ready" | "unconfigured";
    aiProviders: Record<string, "available" | "unavailable">;
  };
}

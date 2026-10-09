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
  target_entity_name?: string;
  primaryUrl?: string;
  primary_url?: string;
  summaryNote?: string;
  summary_note?: string;
  initialEvidenceItems?: Array<{
    mediaType?: EvidenceMediaType;
    media_type?: EvidenceMediaType;
    contentPayload?: string;
    content_payload?: string;
    sourceOrigin?: string;
    source_origin?: string;
    tags?: string[];
  }>;
  initial_evidence_items?: Array<{
    mediaType?: EvidenceMediaType;
    media_type?: EvidenceMediaType;
    contentPayload?: string;
    content_payload?: string;
    sourceOrigin?: string;
    source_origin?: string;
    tags?: string[];
  }>;
}

export interface InvestigationManifest {
  investigationId?: string;
  investigation_id?: string;
  createdAt?: string;
  created_at?: string;
  engineSemver?: string;
  engine_semver?: string;
  scoringAlgorithmVersion?: string;
  scoring_algorithm_version?: string;
  analyzerVersions?: Record<string, string>;
  analyzer_versions?: Record<string, string>;
  configurationDigest?: string;
  configuration_digest?: string;
  inputDigest?: string;
  input_digest?: string;
}

export interface InvestigationResponse {
  id: string;
  status: InvestigationStatus;
  title: string;
  targetEntityName?: string;
  target_entity_name?: string;
  primaryUrl?: string;
  primary_url?: string;
  evidenceCount?: number;
  evidence_count?: number;
  evidence: CanonicalEvidenceItem[];
  riskAssessment?: DeterministicRiskAssessment;
  risk_assessment?: DeterministicRiskAssessment;
  analyzerRecords?: AnalyzerExecutionRecord[];
  analyzer_records?: AnalyzerExecutionRecord[];
  manifest: InvestigationManifest;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
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

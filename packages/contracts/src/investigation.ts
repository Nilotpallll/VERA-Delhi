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

// ── Phase 6: VERA Agent Contracts ────────────────────────────────────────────

/** Request body for POST /investigations/{id}/run-agent */
export interface AgentRunRequest {
  /** Raw inputs for the investigator agent */
  inputs: Array<{
    type: string;         // "text" | "url" | "image" | "audio" | "video" | "apk"
    value: string;        // The content or URL
    description?: string;
    source_label?: string;
    metadata?: Record<string, unknown>;
  }>;
  /** Max agentic loop iterations (default 5) */
  max_iterations?: number;
}

/** Response from POST /investigations/{id}/run-agent */
export interface AgentRunResponse {
  investigation_id: string;
  status: string;
  risk_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  investigation_status: string;
  evidence_count: number;
  entity_count: number;
  message: string;
  ruleset_version: string;
  generated_at: string;
}

/** A suspicious indicator detected by the risk engine */
export interface SuspiciousIndicator {
  signal_type: string;
  weight: number;
  description: string;
  source: string;
}

/** Full forensic report from GET /investigations/{id}/agent-report */
export interface AgentForensicReport {
  investigation_id: string;
  report: {
    investigation_id: string;
    generated_at: string;
    executive_summary: string;
    risk_score: number;
    risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
    investigation_status: string;
    model_confidence: number;
    detected_entities: Array<Record<string, unknown>>;
    claims: Array<Record<string, unknown>>;
    evidence: Array<Record<string, unknown>>;
    verification_results: Array<Record<string, unknown>>;
    sebi_guidance_matches: Array<Record<string, unknown>>;
    suspicious_indicators: SuspiciousIndicator[];
    scam_lifecycle_stage: string;
    missing_evidence: string[];
    recommended_actions: string[];
    source_citations: Array<Record<string, unknown>>;
    disclaimer: string;
    ruleset_version: string;
  };
  risk_score: number;
  risk_level: string;
  investigation_status: string;
  evidence_count: number;
  entity_count: number;
  generated_at: string;
  ruleset_version: string;
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


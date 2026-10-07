-- Baseline Migration for VERA Investment-Fraud Platform
-- Enforcing Canonical Evidence Schema (Rule 5) and Tri-State Verification (Rule 8)

-- Enable pgvector extension for dense semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Investigations Master Table
CREATE TABLE IF NOT EXISTS investigations (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    target_entity_name VARCHAR(255),
    primary_url TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    manifest JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Canonical Evidence Table (Rule 5 & Rule 10: Storage isolation)
CREATE TABLE IF NOT EXISTS canonical_evidence (
    id VARCHAR(64) PRIMARY KEY,
    investigation_id VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    media_type VARCHAR(32) NOT NULL,
    sha256 CHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    source_origin TEXT NOT NULL,
    storage_ref JSONB, -- { bucket, storage_path, provider, mime_type, size_bytes }
    content_payload TEXT,
    extracted_entities JSONB DEFAULT '{}'::jsonb,
    verification_state VARCHAR(32) NOT NULL DEFAULT 'UNAVAILABLE', -- VERIFIED, NOT_VERIFIED, UNAVAILABLE (Rule 8)
    verification_details JSONB NOT NULL,
    embedding vector(1024), -- BGE-M3 1024-dim embedding
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_investigation ON canonical_evidence(investigation_id);
CREATE INDEX IF NOT EXISTS idx_evidence_sha256 ON canonical_evidence(sha256);

-- Analyzer Execution Audit Trail (Rule 12 & Rule 13)
CREATE TABLE IF NOT EXISTS analyzer_execution_records (
    id BIGSERIAL PRIMARY KEY,
    investigation_id VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    evidence_id VARCHAR(64) REFERENCES canonical_evidence(id) ON DELETE SET NULL,
    analyzer_name VARCHAR(128) NOT NULL,
    analyzer_version VARCHAR(32) NOT NULL,
    weights_digest VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL, -- SUCCESS, FAILED, TIMED_OUT, SKIPPED (Rule 9)
    execution_duration_ms DOUBLE PRECISION NOT NULL,
    uncertainty DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    findings JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Deterministic Risk Assessments (Rule 6 & Rule 7)
CREATE TABLE IF NOT EXISTS deterministic_risk_assessments (
    id BIGSERIAL PRIMARY KEY,
    investigation_id VARCHAR(64) UNIQUE NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    final_score DOUBLE PRECISION NOT NULL,
    tier VARCHAR(32) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW, SAFE, INCONCLUSIVE
    factors JSONB NOT NULL,
    uncertainty_penalty DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    algorithm_version VARCHAR(32) NOT NULL,
    summary TEXT NOT NULL,
    is_llm_assigned BOOLEAN NOT NULL DEFAULT FALSE, -- Must ALWAYS be FALSE
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

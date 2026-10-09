-- Phase 2 Migration: VERA Canonical Investigation & Evidence System
-- Implements all 12 tables with full constraint enforcement
-- Architecture Rules: 5, 8, 9, 10, 12, 13

-- ── Extensions ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          VARCHAR(64) PRIMARY KEY,
    email       VARCHAR(320) UNIQUE,
    display_name VARCHAR(255),
    roles       JSONB NOT NULL DEFAULT '["investigator"]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Investigations ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS investigations (
    id                  VARCHAR(64) PRIMARY KEY,
    status              VARCHAR(32) NOT NULL DEFAULT 'QUEUED',
    title               VARCHAR(255) NOT NULL,
    target_entity_name  VARCHAR(255),
    primary_url         TEXT,
    summary_note        TEXT,
    submitted_by        VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    risk_score          DOUBLE PRECISION,
    risk_tier           VARCHAR(32),
    risk_summary        TEXT,
    manifest            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_investigations_status CHECK (
        status IN ('QUEUED','RUNNING','PARTIAL','COMPLETED','FAILED','INSUFFICIENT_EVIDENCE')
    ),
    CONSTRAINT ck_investigations_risk_score CHECK (
        risk_score IS NULL OR (risk_score >= 0.0 AND risk_score <= 100.0)
    )
);
CREATE INDEX IF NOT EXISTS ix_investigations_status ON investigations(status);
CREATE INDEX IF NOT EXISTS ix_investigations_submitted_by ON investigations(submitted_by);

-- ── Inputs ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inputs (
    id                VARCHAR(64) PRIMARY KEY,
    investigation_id  VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    type              VARCHAR(64) NOT NULL,
    value             TEXT NOT NULL,
    description       TEXT,
    source_label      VARCHAR(255),
    submitted_by      VARCHAR(64),
    extra_metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_inputs_investigation ON inputs(investigation_id);

-- ── Evidence (canonical, append-only, Rule 5 & Rule 9) ───────────────────────
-- No updated_at column — evidence is immutable
CREATE TABLE IF NOT EXISTS evidence (
    id                VARCHAR(64) PRIMARY KEY,
    investigation_id  VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    type              VARCHAR(128) NOT NULL,
    category          VARCHAR(64) NOT NULL,
    severity          VARCHAR(32) NOT NULL,
    confidence        DOUBLE PRECISION,       -- NULL when not applicable
    description       TEXT NOT NULL,
    source_type       VARCHAR(64) NOT NULL,   -- Rule 5 source provenance
    source_reference  VARCHAR(255) NOT NULL,
    analyzer          VARCHAR(128),
    analyzer_version  VARCHAR(32),
    extra_metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- immutable timestamp

    CONSTRAINT ck_evidence_severity CHECK (
        severity IN ('CRITICAL','HIGH','MEDIUM','LOW','INFO')
    ),
    CONSTRAINT ck_evidence_confidence CHECK (
        confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)
    ),
    CONSTRAINT ck_evidence_source_type CHECK (
        source_type IN (
            'user_input','llm','ml_model','ocr','stt',
            'deterministic_analyzer','official_source','web_source','database','system'
        )
    )
);
CREATE INDEX IF NOT EXISTS ix_evidence_investigation ON evidence(investigation_id);
CREATE INDEX IF NOT EXISTS ix_evidence_type ON evidence(type);
CREATE INDEX IF NOT EXISTS ix_evidence_severity ON evidence(severity);
CREATE INDEX IF NOT EXISTS ix_evidence_source_type ON evidence(source_type);
CREATE INDEX IF NOT EXISTS ix_evidence_inv_type ON evidence(investigation_id, type);

-- ── Entities ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS entities (
    id                    VARCHAR(64) PRIMARY KEY,
    investigation_id      VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    type                  VARCHAR(64) NOT NULL,
    value                 TEXT NOT NULL,
    display_name          VARCHAR(255),
    confidence            DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    source_evidence_ids   JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_input_ids      JSONB NOT NULL DEFAULT '[]'::jsonb,
    verification_json     JSONB,
    extra_metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_entity_type CHECK (
        type IN ('PERSON','COMPANY','PHONE','EMAIL','UPI','DOMAIN','URL',
                 'PROFILE','APK','MESSAGE','IMAGE','VIDEO','AUDIO')
    ),
    CONSTRAINT uq_entity_inv_type_value UNIQUE (investigation_id, type, value)
);
CREATE INDEX IF NOT EXISTS ix_entities_investigation ON entities(investigation_id);
CREATE INDEX IF NOT EXISTS ix_entities_type ON entities(type);

-- ── Relationships ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS relationships (
    id                  VARCHAR(64) PRIMARY KEY,
    investigation_id    VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    source_entity_id    VARCHAR(64) NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id    VARCHAR(64) NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type   VARCHAR(64) NOT NULL,
    confidence          DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    evidence_ids        JSONB NOT NULL DEFAULT '[]'::jsonb,
    extra_metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_relationship_type CHECK (
        relationship_type IN (
            'OWNS','CONTROLS','PROMOTES','ASSOCIATED_WITH','IMPERSONATES',
            'COMMUNICATES_WITH','HOSTS','SENDS','MENTIONED_IN','LINKED_TO'
        )
    )
);
CREATE INDEX IF NOT EXISTS ix_relationships_investigation ON relationships(investigation_id);
CREATE INDEX IF NOT EXISTS ix_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS ix_relationships_target ON relationships(target_entity_id);

-- ── Claims ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS claims (
    id                      VARCHAR(64) PRIMARY KEY,
    investigation_id        VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    claim_text              TEXT NOT NULL,
    claim_type              VARCHAR(128) NOT NULL,
    status                  VARCHAR(32) NOT NULL DEFAULT 'UNVERIFIED',
    source_input_ids        JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_evidence_ids     JSONB NOT NULL DEFAULT '[]'::jsonb,
    supporting_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    refuting_evidence_ids   JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence              DOUBLE PRECISION,
    extra_metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_claim_status CHECK (
        status IN ('UNVERIFIED','SUPPORTED','REFUTED','INCONCLUSIVE')
    )
);
CREATE INDEX IF NOT EXISTS ix_claims_investigation ON claims(investigation_id);
CREATE INDEX IF NOT EXISTS ix_claims_status ON claims(status);

-- ── Verification Results (Rule 8 tri-state) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS verification_results (
    id                   VARCHAR(64) PRIMARY KEY,
    investigation_id     VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    entity_id            VARCHAR(64) REFERENCES entities(id) ON DELETE SET NULL,
    claim_id             VARCHAR(64) REFERENCES claims(id) ON DELETE SET NULL,
    checker              VARCHAR(128) NOT NULL,
    checker_version      VARCHAR(32) NOT NULL,
    verification_state   VARCHAR(32) NOT NULL,   -- VERIFIED | NOT_VERIFIED | UNAVAILABLE
    source_type          VARCHAR(64) NOT NULL,
    confidence           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    details              TEXT NOT NULL,
    raw_response_hash    VARCHAR(64),
    has_analyzer_failure BOOLEAN NOT NULL DEFAULT FALSE,
    extra_metadata       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_verification_state CHECK (
        verification_state IN ('VERIFIED','NOT_VERIFIED','UNAVAILABLE')
    )
);
CREATE INDEX IF NOT EXISTS ix_vr_investigation ON verification_results(investigation_id);
CREATE INDEX IF NOT EXISTS ix_vr_state ON verification_results(verification_state);

-- ── Risk Signals (deterministic, Rules 6 & 7) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_signals (
    id                    VARCHAR(64) PRIMARY KEY,
    investigation_id      VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    signal_type           VARCHAR(128) NOT NULL,
    severity              VARCHAR(32) NOT NULL,
    score_contribution    DOUBLE PRECISION NOT NULL,
    weight                DOUBLE PRECISION NOT NULL,
    source_evidence_ids   JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_type           VARCHAR(64) NOT NULL,
    deterministic_rule_id VARCHAR(128) NOT NULL,
    description           TEXT NOT NULL,
    extra_metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_risk_signal_score CHECK (
        score_contribution >= 0.0 AND score_contribution <= 100.0
    ),
    CONSTRAINT ck_risk_signal_weight CHECK (
        weight >= 0.0 AND weight <= 1.0
    )
);
CREATE INDEX IF NOT EXISTS ix_risk_signals_investigation ON risk_signals(investigation_id);
CREATE INDEX IF NOT EXISTS ix_risk_signals_severity ON risk_signals(severity);

-- ── Model Runs (Rules 12 & 13) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_runs (
    id                    VARCHAR(64) PRIMARY KEY,
    investigation_id      VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    input_id              VARCHAR(64) REFERENCES inputs(id) ON DELETE SET NULL,
    evidence_id           VARCHAR(64) REFERENCES evidence(id) ON DELETE SET NULL,
    model_name            VARCHAR(128) NOT NULL,
    model_version         VARCHAR(64) NOT NULL,
    model_weights_digest  VARCHAR(128) NOT NULL,
    provider              VARCHAR(64) NOT NULL,
    prompt_digest         VARCHAR(64),
    output_summary        TEXT,
    output_raw            JSONB NOT NULL DEFAULT '{}'::jsonb,
    latency_ms            DOUBLE PRECISION NOT NULL,
    success               BOOLEAN NOT NULL DEFAULT TRUE,
    error_message         TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_model_runs_investigation ON model_runs(investigation_id);

-- ── Analyzer Runs (Rules 4, 9, 12) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analyzer_runs (
    id                   VARCHAR(64) PRIMARY KEY,
    investigation_id     VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    input_id             VARCHAR(64) REFERENCES inputs(id) ON DELETE SET NULL,
    evidence_id          VARCHAR(64) REFERENCES evidence(id) ON DELETE SET NULL,
    analyzer_name        VARCHAR(128) NOT NULL,
    analyzer_version     VARCHAR(64) NOT NULL,
    weights_digest       VARCHAR(128) NOT NULL,
    status               VARCHAR(32) NOT NULL,  -- SUCCESS | FAILED | TIMED_OUT | SKIPPED
    started_at           TIMESTAMPTZ NOT NULL,
    completed_at         TIMESTAMPTZ NOT NULL,
    duration_ms          DOUBLE PRECISION NOT NULL,
    findings             JSONB NOT NULL DEFAULT '{}'::jsonb,
    uncertainty          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    error_message        TEXT,
    failure_evidence_id  VARCHAR(64),  -- SYSTEM evidence created on failure (Rule 9)
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_analyzer_status CHECK (
        status IN ('SUCCESS','FAILED','TIMED_OUT','SKIPPED')
    ),
    CONSTRAINT ck_analyzer_uncertainty CHECK (
        uncertainty >= 0.0 AND uncertainty <= 1.0
    )
);
CREATE INDEX IF NOT EXISTS ix_analyzer_runs_investigation ON analyzer_runs(investigation_id);
CREATE INDEX IF NOT EXISTS ix_analyzer_runs_status ON analyzer_runs(status);

-- ── Reports (Rule 13 — reproducible) ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reports (
    id                         VARCHAR(64) PRIMARY KEY,
    investigation_id           VARCHAR(64) NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    status                     VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    version                    INTEGER NOT NULL DEFAULT 1,
    executive_summary          TEXT NOT NULL,
    risk_score                 DOUBLE PRECISION NOT NULL,
    risk_tier                  VARCHAR(32) NOT NULL,
    evidence_ids               JSONB NOT NULL DEFAULT '[]'::jsonb,
    entity_ids                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    claim_ids                  JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_signal_ids            JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_run_ids              JSONB NOT NULL DEFAULT '[]'::jsonb,
    analyzer_run_ids           JSONB NOT NULL DEFAULT '[]'::jsonb,
    engine_version             VARCHAR(32) NOT NULL,
    scoring_algorithm_version  VARCHAR(64) NOT NULL,
    generated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_report_status CHECK (status IN ('DRAFT','FINAL','SUPERSEDED')),
    CONSTRAINT ck_report_risk_score CHECK (risk_score >= 0.0 AND risk_score <= 100.0)
);
CREATE INDEX IF NOT EXISTS ix_reports_investigation ON reports(investigation_id);

-- ── Audit Logs (immutable) ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id               VARCHAR(64) PRIMARY KEY,
    investigation_id VARCHAR(64) REFERENCES investigations(id) ON DELETE SET NULL,
    actor_type       VARCHAR(32) NOT NULL,
    actor_id         VARCHAR(128) NOT NULL,
    action           VARCHAR(128) NOT NULL,
    target_type      VARCHAR(64),
    target_id        VARCHAR(128),
    details          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_investigation ON audit_logs(investigation_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at);

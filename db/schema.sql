-- Global, platform-agnostic logical schema for PostgreSQL.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS businesses (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, country_code CHAR(2) NOT NULL,
    business_type TEXT NOT NULL, channel TEXT NOT NULL, location TEXT,
    website_url TEXT, goal TEXT, profile_json JSONB NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS platform_connections (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL, country_code CHAR(2) NOT NULL,
    platform TEXT NOT NULL, category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', capabilities_json JSONB NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS competitors (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL, name TEXT NOT NULL,
    platform TEXT NOT NULL, strategic BOOLEAN NOT NULL DEFAULT FALSE,
    similarity_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    market_relevance DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, name TEXT NOT NULL,
    category TEXT, current_price DOUBLE PRECISION, currency TEXT
);
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, captured_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL, source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS changes (
    id TEXT PRIMARY KEY, business_id TEXT, competitor_id TEXT NOT NULL, type TEXT NOT NULL,
    before_json JSONB, after_json JSONB, detected_at TIMESTAMPTZ NOT NULL,
    magnitude DOUBLE PRECISION NOT NULL DEFAULT 0, severity TEXT NOT NULL DEFAULT 'info',
    impact_score DOUBLE PRECISION NOT NULL DEFAULT 0, confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    evidence_json JSONB NOT NULL DEFAULT '[]', source TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, rating DOUBLE PRECISION,
    text TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, sentiment TEXT,
    topics_json JSONB NOT NULL DEFAULT '[]', product_id TEXT,
    source TEXT NOT NULL DEFAULT '', confidence DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS cost_signals (
    id TEXT PRIMARY KEY, product_id TEXT, type TEXT NOT NULL, name TEXT NOT NULL,
    before_value DOUBLE PRECISION, after_value DOUBLE PRECISION, unit TEXT NOT NULL DEFAULT '',
    observed_at TIMESTAMPTZ NOT NULL, source TEXT NOT NULL DEFAULT '',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, prediction_type TEXT NOT NULL,
    predicted_at TIMESTAMPTZ NOT NULL, expected_window_days INTEGER NOT NULL,
    probability DOUBLE PRECISION NOT NULL, evidence_json JSONB NOT NULL DEFAULT '[]',
    outcome TEXT, outcome_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, change_id TEXT NOT NULL,
    payload_json JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_changes_competitor_detected ON changes (competitor_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_changes_business_detected ON changes (business_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_competitor_created ON reviews (competitor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_competitor_predicted ON predictions (competitor_id, predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_competitor_captured ON snapshots (competitor_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_competitor_created ON alerts (competitor_id, created_at DESC);


CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, definition_key TEXT NOT NULL,
    signal_kind TEXT NOT NULL, direction TEXT NOT NULL,
    current_value DOUBLE PRECISION NOT NULL, reference_value DOUBLE PRECISION,
    delta DOUBLE PRECISION, delta_pct DOUBLE PRECISION, detected_at TIMESTAMPTZ NOT NULL,
    observation_ids_json JSONB NOT NULL DEFAULT '[]', measurement_ids_json JSONB NOT NULL DEFAULT '[]',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5, significance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    knowledge_kind TEXT NOT NULL DEFAULT 'estimate', rationale TEXT NOT NULL DEFAULT '',
    freshness_minutes INTEGER
);
CREATE INDEX IF NOT EXISTS idx_signals_entity_definition_detected
    ON signals (entity_id, definition_key, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_significance_detected
    ON signals (significance DESC, detected_at DESC);


CREATE TABLE IF NOT EXISTS business_impacts (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL, entity_id TEXT NOT NULL,
    signal_id TEXT NOT NULL, factor_key TEXT NOT NULL,
    exposure DOUBLE PRECISION NOT NULL DEFAULT 0.5, magnitude DOUBLE PRECISION NOT NULL,
    magnitude_low DOUBLE PRECISION, magnitude_high DOUBLE PRECISION,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5, significance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    rationale TEXT NOT NULL DEFAULT '',
    evidence_ids_json JSONB NOT NULL DEFAULT '[]',
    observation_ids_json JSONB NOT NULL DEFAULT '[]',
    measurement_ids_json JSONB NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_business_impacts_business_priority
    ON business_impacts (business_id, significance DESC);
CREATE INDEX IF NOT EXISTS idx_business_impacts_signal
    ON business_impacts (signal_id);

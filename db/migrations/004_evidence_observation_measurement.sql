CREATE TABLE IF NOT EXISTS evidence_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    source_type TEXT NOT NULL,
    access_method TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    reliability DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    coverage DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    content_hash TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES evidence_sources(id),
    statement TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    locator TEXT,
    excerpt TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    knowledge_kind TEXT NOT NULL DEFAULT 'fact'
);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    metric TEXT NOT NULL,
    raw_value JSONB NOT NULL,
    normalized_value DOUBLE PRECISION,
    unit TEXT,
    currency TEXT,
    geography TEXT,
    observed_at TIMESTAMPTZ NOT NULL,
    source_id TEXT NOT NULL REFERENCES evidence_sources(id),
    evidence_id TEXT REFERENCES evidence(id),
    access_method TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    knowledge_kind TEXT NOT NULL DEFAULT 'fact',
    provenance_json JSONB NOT NULL DEFAULT '{}',
    model_version TEXT
);

CREATE TABLE IF NOT EXISTS measurements (
    id TEXT PRIMARY KEY,
    definition_key TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL,
    time_window TEXT NOT NULL,
    geography TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    quality TEXT NOT NULL DEFAULT 'raw',
    formula TEXT NOT NULL,
    model_version TEXT,
    observation_ids_json JSONB NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_observations_entity_metric_time
    ON observations (entity_id, metric, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_source_captured
    ON evidence (source_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_entity_definition_time
    ON measurements (entity_id, definition_key, measured_at DESC);

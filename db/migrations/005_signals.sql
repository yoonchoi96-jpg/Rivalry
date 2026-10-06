CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    definition_key TEXT NOT NULL,
    signal_kind TEXT NOT NULL,
    direction TEXT NOT NULL,
    current_value DOUBLE PRECISION NOT NULL,
    reference_value DOUBLE PRECISION,
    delta DOUBLE PRECISION,
    delta_pct DOUBLE PRECISION,
    detected_at TIMESTAMPTZ NOT NULL,
    observation_ids_json JSONB NOT NULL DEFAULT '[]',
    measurement_ids_json JSONB NOT NULL DEFAULT '[]',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    significance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    rationale TEXT NOT NULL DEFAULT '',
    freshness_minutes INTEGER
);

CREATE INDEX IF NOT EXISTS idx_signals_entity_definition_detected
    ON signals (entity_id, definition_key, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_significance_detected
    ON signals (significance DESC, detected_at DESC);

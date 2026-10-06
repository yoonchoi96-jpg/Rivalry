CREATE TABLE IF NOT EXISTS business_impacts (
    id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    signal_id TEXT NOT NULL,
    factor_key TEXT NOT NULL,
    exposure DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    magnitude DOUBLE PRECISION NOT NULL,
    magnitude_low DOUBLE PRECISION,
    magnitude_high DOUBLE PRECISION,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    significance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    rationale TEXT NOT NULL DEFAULT '',
    evidence_ids_json JSONB NOT NULL DEFAULT '[]',
    observation_ids_json JSONB NOT NULL DEFAULT '[]',
    measurement_ids_json JSONB NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_business_impacts_business_priority
    ON business_impacts (business_id, significance DESC);
CREATE INDEX IF NOT EXISTS idx_business_impacts_signal
    ON business_impacts (signal_id);

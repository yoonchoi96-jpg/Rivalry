CREATE TABLE IF NOT EXISTS source_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    reliability DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    coverage DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    cost DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    latency DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    freshness_minutes INTEGER,
    rate_limit_per_minute INTEGER,
    normalization_quality DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    capabilities_json JSONB NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_source_profiles_kind_reliability
    ON source_profiles (kind, reliability DESC);

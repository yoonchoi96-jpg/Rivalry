CREATE TABLE IF NOT EXISTS decision_recommendations (
    impact_id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL,
    signal_id TEXT NOT NULL,
    action TEXT NOT NULL,
    priority DOUBLE PRECISION NOT NULL,
    rationale TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    factor_key TEXT NOT NULL,
    policy_id TEXT,
    recommendation_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decision_recommendations_business
    ON decision_recommendations (business_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_decision_recommendations_signal
    ON decision_recommendations (signal_id);

CREATE TABLE IF NOT EXISTS decision_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    policy_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

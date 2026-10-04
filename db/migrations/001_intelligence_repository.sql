-- PostgreSQL migration for the durable intelligence repository.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE changes ADD COLUMN IF NOT EXISTS business_id TEXT;
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS product_id TEXT;

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    competitor_id TEXT NOT NULL,
    change_id TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_changes_competitor_detected
    ON changes (competitor_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_changes_business_detected
    ON changes (business_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_competitor_created
    ON reviews (competitor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_competitor_predicted
    ON predictions (competitor_id, predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_competitor_captured
    ON snapshots (competitor_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_competitor_created
    ON alerts (competitor_id, created_at DESC);

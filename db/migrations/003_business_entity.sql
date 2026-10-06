-- Business Entity persistence additions for existing installations.
ALTER TABLE businesses
    ADD COLUMN IF NOT EXISTS profile_json JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_businesses_country_type
    ON businesses (country_code, business_type);

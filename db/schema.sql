CREATE TABLE IF NOT EXISTS businesses (id TEXT PRIMARY KEY, name TEXT NOT NULL, plan TEXT NOT NULL DEFAULT 'free', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS competitors (id TEXT PRIMARY KEY, business_id TEXT NOT NULL, name TEXT NOT NULL, platform TEXT NOT NULL, strategic INTEGER NOT NULL DEFAULT 0, similarity_score REAL NOT NULL DEFAULT 0, market_relevance REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, captured_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS changes (id TEXT PRIMARY KEY, competitor_id TEXT NOT NULL, type TEXT NOT NULL, before_value TEXT, after_value TEXT, magnitude REAL NOT NULL DEFAULT 0, severity TEXT NOT NULL DEFAULT 'info', impact_score REAL NOT NULL DEFAULT 0, confidence REAL NOT NULL DEFAULT 0, detected_at TEXT NOT NULL, source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS recommendations (id TEXT PRIMARY KEY, change_id TEXT NOT NULL, action TEXT NOT NULL, reason TEXT NOT NULL, confidence REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_competitors_business ON competitors(business_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_competitor_time ON snapshots(competitor_id,captured_at);
CREATE INDEX IF NOT EXISTS idx_changes_impact ON changes(impact_score DESC);

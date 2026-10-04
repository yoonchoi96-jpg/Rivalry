# RIVALRY INITIAL AUDIT

Based on the repository state at commit `277bbfb` (main). Baseline: 72 tests pass, 1 skipped (PostgreSQL integration).

## 1. Repository Architecture
FastAPI app (`api/`), job runtime (`core/jobs/`), AI layer (`core/ai/`), intelligence store/alerts/prediction (`core/intelligence/`), deterministic engines (`engines/`), adapter interfaces (`adapters/`), SQL migrations (`db/`). Entry points: `api.main:app` (Dockerfile), `rivalry-worker` (`core.jobs.entrypoint:run_worker`), `worker.py`. Many directories (`core/auth`, `billing`, `audit`, `notifications`, `engines/pricing|product|promotion`) are `.gitkeep` placeholders only.

## 2. Current Data Model
Pydantic models for Business, Competitor, Change, Recommendation, Prediction, Job. Persistence: `InMemoryIntelligenceRepository` and `PostgresIntelligenceRepository` (`db/migrations/001`), jobs + `job_outbox` (`db/migrations/002`). Competitor/Change API routes still use process-local state.

## 3. Collection / Adapter Layer
Only `adapters/base.py` and `registry.py` exist; no concrete source adapter is implemented. Collection is not yet real.

## 4. Snapshot System
Snapshot is a core object, and the detector compares snapshots. Verify immutability and a stable snapshot identity/provenance (source URL, fetched_at, content hash) before adding collectors.

## 5. Change Detection
`engines/change_detection` (detector, scoring, service): deterministic diff plus impact score with tests. Noise filtering vs. meaningful change should be formalized (thresholds, ignored fields).

## 6. AI Layer
Gateway, router, adaptive router, provider health, runtime with tool-calling, multi-AI orchestrator, evidence and quality modules. Providers: OpenAI, Anthropic, Gemini, Perplexity, Naver, Qwen, DeepSeek, xAI. AI output must stay separate from raw data.

## 7. Recommendation Engine
`engines/recommendation/service.py`: rule-based; limited. Must link evidence and confidence before expansion.

## 8. Queue / Worker Architecture
PostgreSQL job store (statuses, attempts, `max_attempts`, `next_attempt_at`, unique `idempotency_key`) + transactional outbox + Redis Streams queue; worker with retry/backoff, ack, dead-letter and follow-up jobs. Largely implemented; verify crash recovery of pending Redis messages.

## 9. API
`/health`; `/api/v1`: `competitors` (GET/POST), `changes` (GET), `onboarding/state`, `ai/research`, `ai/chat`, `jobs` (POST, GET by id). No authentication on any route. No endpoints for snapshots, signals, recommendations, or job listing/DLQ.

## 10. Tests / CI
Single CI job running `pytest -q` on Python 3.12 (green). Missing: lint, type checking, coverage, Postgres/Redis integration run. Found and fixed: `/ai/chat` raised `NameError` (`_intelligence_store`), masked as HTTP 502.

## 11. Security
`.env` was ignored; secrets read only from env vars; no hard-coded keys found. Gaps: unauthenticated API, no rate limiting, `core/auth` empty, CI lacked explicit `permissions`. Mitigated here: `.env.example`, stricter `.gitignore`, least-privilege workflow permissions.

## 12. Cost
Multi-AI orchestrator can fan out to several providers per request; no caching or per-business budget visibly enforced. Add cache by evidence hash and record token/cost usage (`core/usage`).

## 13. Data Quality
No normalization for currency/units, no stable competitor/product identity across sources, provenance fields not enforced.

## 14. Long-Term Competitive Intelligence Architecture
Preserve: snapshot vs. change vs. signal vs. recommendation separation; adapters isolated from the core; evidence/provenance on every AI conclusion; idempotent jobs; recommend-only (no autonomous actions).

## 15. Current Risks
1. (High) Unauthenticated API with AI endpoints that cost money.
2. (High) API state for competitors/changes not durable.
3. (Medium) No real adapters; no provenance enforcement.
4. (Medium) Weak CI (no lint/types/integration).
5. (Low) Placeholder directories imply features that do not exist.

## 16. Recommended Roadmap
- **P0:** data safety (no destructive migrations), secrets hygiene, API auth.
- **P1:** persistent competitors/changes; DLQ/recovery integration tests with Postgres+Redis in CI.
- **P2:** first concrete adapter with provenance; normalization.
- **P3:** noise vs. meaningful change rules; signal classification.
- **P4:** evidence-linked recommendations; AI caching and cost tracking.
- **P5/P6:** API/alert surface; Nayvadius/Obsidian and Abraham integrations (only after the model stabilizes).

## 17. SAFE FIRST CHANGE
Fix the `/ai/chat` NameError (done), add hermetic test fixtures and CI quality checks, and document configuration. All are low-risk and do not touch data.

# Rivalry Architecture

Collect → Normalize → Detect → Score → Recommend → Alert

Core objects: Business, Product, Competitor, Snapshot, Change, Recommendation, Prediction.

MVP implements the deterministic foundation for future Memory, Pattern and Prediction layers.

## Components

- `api/` – FastAPI routes (`/health`, `/api/v1/...`).
- `core/jobs/` – job models, PostgreSQL store, transactional outbox, Redis Streams queue, worker (retry, dead-letter, follow-up jobs).
- `core/intelligence/` – repositories (in-memory, PostgreSQL), alerts, prediction.
- `core/ai/` – providers, routing, runtime, multi-AI orchestrator, evidence/quality.
- `engines/` – deterministic engines (change detection, scoring, recommendation, review).
- `adapters/` – source adapters; source-specific logic must live here, not in the core.
- `db/` – schema and forward-only migrations (`python -m db.migrate`).

## Principles

Deterministic code collects, normalizes, compares, and scores; AI interprets and never overwrites raw data. Snapshots are immutable, jobs are idempotent, and failed jobs are never silently dropped. Rivalry recommends but does not act autonomously. See [docs/AUDIT.md](docs/AUDIT.md) for the current state and roadmap.

from __future__ import annotations

import os

from core.intelligence.engine import IntelligenceStore
from core.intelligence.postgres_repository import PostgresIntelligenceRepository
from .queue import InMemoryJobQueue


def _build_intelligence_store() -> IntelligenceStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if dsn:
        return IntelligenceStore(repository=PostgresIntelligenceRepository(dsn))
    return IntelligenceStore()


# API and worker processes converge on the same durable repository whenever
# RIVALRY_DATABASE_URL is configured. Tests and local development keep the
# in-memory fallback.
job_queue = InMemoryJobQueue()
intelligence_store = _build_intelligence_store()

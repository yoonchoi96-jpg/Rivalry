from __future__ import annotations

import os
import socket

from core.intelligence.engine import IntelligenceStore
from core.intelligence.postgres_repository import PostgresIntelligenceRepository

from .queue import InMemoryJobQueue
from .redis_queue import RedisJobQueue
from .store import InMemoryJobStore
from .postgres_store import PostgresJobStore


def _build_intelligence_store() -> IntelligenceStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if dsn:
        return IntelligenceStore(repository=PostgresIntelligenceRepository(dsn))
    return IntelligenceStore()


def _build_job_store():
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return PostgresJobStore(dsn) if dsn else InMemoryJobStore()


def _build_job_queue():
    store = _build_job_store()
    redis_url = os.getenv("RIVALRY_REDIS_URL", "").strip()
    if redis_url:
        consumer = f"{socket.gethostname()}-{os.getpid()}"
        return RedisJobQueue(redis_url, job_store=store, consumer=consumer)
    return InMemoryJobQueue()


# API and worker processes use Redis + PostgreSQL when both are configured.
# Without them, the existing in-memory path remains the local/test fallback.
job_queue = _build_job_queue()
intelligence_store = _build_intelligence_store()

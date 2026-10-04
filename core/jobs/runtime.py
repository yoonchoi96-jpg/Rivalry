from __future__ import annotations

import os
import socket

from core.intelligence.engine import IntelligenceStore
from core.intelligence.postgres_repository import PostgresIntelligenceRepository

from .queue import InMemoryJobQueue
from .redis_queue import RedisJobQueue
from .store import InMemoryJobStore, JobStore
from .postgres_store import PostgresJobStore


def _build_intelligence_store() -> IntelligenceStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if dsn:
        return IntelligenceStore(repository=PostgresIntelligenceRepository(dsn))
    return IntelligenceStore()


def _build_job_store() -> JobStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return PostgresJobStore(dsn) if dsn else InMemoryJobStore()


job_store = _build_job_store()


def _build_job_queue():
    redis_url = os.getenv("RIVALRY_REDIS_URL", "").strip()
    if redis_url:
        consumer = f"{socket.gethostname()}-{os.getpid()}"
        return RedisJobQueue(redis_url, job_store=job_store, consumer=consumer)
    return InMemoryJobQueue()


# API and worker processes share this durable PostgreSQL job store and Redis queue
# when both production dependencies are configured.
job_queue = _build_job_queue()
intelligence_store = _build_intelligence_store()

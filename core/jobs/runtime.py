from __future__ import annotations

import os
import socket

from core.intelligence.engine import IntelligenceStore
from core.intelligence.postgres_repository import PostgresIntelligenceRepository
from engines.competitor.repository import InMemoryCompetitorRepository, PostgresCompetitorRepository
from engines.competitor.service import CompetitorService
from engines.competitor.repository import InMemoryCompetitorRepository, PostgresCompetitorRepository
from engines.competitor.service import CompetitorService

from .queue import InMemoryJobQueue
from .redis_queue import RedisJobQueue
from .store import InMemoryJobStore, JobStore
from .postgres_store import PostgresJobStore


def _is_production() -> bool:
    return os.getenv("RIVALRY_ENV", "").strip().lower() in {"production", "prod"}


def _build_intelligence_store() -> IntelligenceStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if dsn:
        return IntelligenceStore(repository=PostgresIntelligenceRepository(dsn))
    return IntelligenceStore()


def _build_job_store() -> JobStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return PostgresJobStore(dsn) if dsn else InMemoryJobStore()


def _build_job_queue(*, job_store: JobStore):
    redis_url = os.getenv("RIVALRY_REDIS_URL", "").strip()
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if _is_production() and (not redis_url or not dsn):
        raise RuntimeError(
            "Production runtime requires both RIVALRY_DATABASE_URL and RIVALRY_REDIS_URL"
        )
    if redis_url:
        consumer = f"{socket.gethostname()}-{os.getpid()}"
        return RedisJobQueue(redis_url, job_store=job_store, consumer=consumer)
    return InMemoryJobQueue()


def _build_competitor_service() -> CompetitorService:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    repository = PostgresCompetitorRepository(dsn) if dsn else InMemoryCompetitorRepository()
    return CompetitorService(repository=repository)


job_store = _build_job_store()
job_queue = _build_job_queue(job_store=job_store)
intelligence_store = _build_intelligence_store()


def _build_competitor_service() -> CompetitorService:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    repository = PostgresCompetitorRepository(dsn) if dsn else InMemoryCompetitorRepository()
    return CompetitorService(repository=repository)


competitor_service = _build_competitor_service()
competitor_service = _build_competitor_service()

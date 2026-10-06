from __future__ import annotations

import os
import socket

from core.business.postgres_repository import PostgresBusinessRepository
from core.business.repository import InMemoryBusinessRepository
from core.evidence.postgres_repository import PostgresEvidenceRepository
from core.evidence.repository import InMemoryEvidenceRepository
from core.intelligence.engine import IntelligenceStore
from core.intelligence.postgres_repository import PostgresIntelligenceRepository
from core.measurement.postgres_repository import PostgresMeasurementRepository
from core.measurement.repository import InMemoryMeasurementRepository
from core.observation.postgres_repository import PostgresObservationRepository
from core.observation.repository import InMemoryObservationRepository
from engines.competitor.repository import InMemoryCompetitorRepository, PostgresCompetitorRepository
from engines.competitor.service import CompetitorService
from .queue import InMemoryJobQueue
from .redis_queue import RedisJobQueue
from .store import InMemoryJobStore, JobStore
from .postgres_store import PostgresJobStore


def _is_production() -> bool:
    return os.getenv("RIVALRY_ENV", "").strip().lower() in {"production", "prod"}


def _build_intelligence_store() -> IntelligenceStore:
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    return IntelligenceStore(repository=PostgresIntelligenceRepository(dsn)) if dsn else IntelligenceStore()


def _build_job_store() -> JobStore:
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    return PostgresJobStore(dsn) if dsn else InMemoryJobStore()


def _build_job_queue(*, job_store: JobStore):
    redis_url=os.getenv("RIVALRY_REDIS_URL","").strip()
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    if _is_production() and (not redis_url or not dsn):
        raise RuntimeError("Production runtime requires both RIVALRY_DATABASE_URL and RIVALRY_REDIS_URL")
    if redis_url:
        return RedisJobQueue(redis_url, job_store=job_store, consumer=f"{socket.gethostname()}-{os.getpid()}")
    return InMemoryJobQueue()


def _build_business_repository():
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    return PostgresBusinessRepository(dsn) if dsn else InMemoryBusinessRepository()


def _build_evidence_repository():
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    return PostgresEvidenceRepository(dsn) if dsn else InMemoryEvidenceRepository()


def _build_observation_repository():
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    return PostgresObservationRepository(dsn) if dsn else InMemoryObservationRepository()


def _build_measurement_repository():
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    return PostgresMeasurementRepository(dsn) if dsn else InMemoryMeasurementRepository()


def _build_competitor_service() -> CompetitorService:
    dsn=os.getenv("RIVALRY_DATABASE_URL","").strip()
    repository=PostgresCompetitorRepository(dsn) if dsn else InMemoryCompetitorRepository()
    return CompetitorService(repository=repository)


job_store=_build_job_store()
job_queue=_build_job_queue(job_store=job_store)
intelligence_store=_build_intelligence_store()
business_repository=_build_business_repository()
evidence_repository=_build_evidence_repository()
observation_repository=_build_observation_repository()
measurement_repository=_build_measurement_repository()
competitor_service=_build_competitor_service()

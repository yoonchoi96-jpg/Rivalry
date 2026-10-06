from __future__ import annotations
import os, socket
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
from core.signal.postgres_repository import PostgresSignalRepository
from core.signal.repository import InMemorySignalRepository
from core.impact.postgres_repository import PostgresImpactRepository
from core.impact.repository import InMemoryImpactRepository
from core.source.postgres_repository import PostgresSourceRepository
from core.source.repository import InMemorySourceRepository
from engines.competitor.repository import InMemoryCompetitorRepository, PostgresCompetitorRepository
from engines.competitor.service import CompetitorService
from .queue import InMemoryJobQueue
from .redis_queue import RedisJobQueue
from .store import InMemoryJobStore, JobStore
from .postgres_store import PostgresJobStore

def _is_production() -> bool:
    return os.getenv("RIVALRY_ENV", "").strip().lower() in {"production", "prod"}

def _build_job_store() -> JobStore:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return PostgresJobStore(dsn) if dsn else InMemoryJobStore()

def _build_job_queue(*, job_store: JobStore):
    redis_url, dsn = os.getenv("RIVALRY_REDIS_URL", "").strip(), os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if _is_production() and (not redis_url or not dsn):
        raise RuntimeError("Production runtime requires both RIVALRY_DATABASE_URL and RIVALRY_REDIS_URL")
    return RedisJobQueue(redis_url, job_store=job_store, consumer=f"{socket.gethostname()}-{os.getpid()}") if redis_url else InMemoryJobQueue()

def _repo(pg, mem):
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return pg(dsn) if dsn else mem()

def _build_intelligence_store():
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return IntelligenceStore(repository=PostgresIntelligenceRepository(dsn)) if dsn else IntelligenceStore()

business_repository = _repo(PostgresBusinessRepository, InMemoryBusinessRepository)
evidence_repository = _repo(PostgresEvidenceRepository, InMemoryEvidenceRepository)
observation_repository = _repo(PostgresObservationRepository, InMemoryObservationRepository)
measurement_repository = _repo(PostgresMeasurementRepository, InMemoryMeasurementRepository)
signal_repository = _repo(PostgresSignalRepository, InMemorySignalRepository)
impact_repository = _repo(PostgresImpactRepository, InMemoryImpactRepository)
source_repository = _repo(PostgresSourceRepository, InMemorySourceRepository)
job_store = _build_job_store()
job_queue = _build_job_queue(job_store=job_store)
intelligence_store = _build_intelligence_store()

def _build_competitor_service() -> CompetitorService:
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    return CompetitorService(repository=PostgresCompetitorRepository(dsn) if dsn else InMemoryCompetitorRepository())

competitor_service = _build_competitor_service()

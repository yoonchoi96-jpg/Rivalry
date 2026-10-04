from core.jobs.models import Job, JobType
from core.jobs.store import InMemoryJobStore


def test_in_memory_job_store_round_trip_is_copy():
    store = InMemoryJobStore()
    job = Job(type=JobType.COLLECT_COMPETITOR)
    store.save(job)
    loaded = store.get(job.id)
    assert loaded is not None
    loaded.attempts = 2
    assert store.get(job.id).attempts == 0


def test_in_memory_job_store_deduplicates_idempotency_key():
    store = InMemoryJobStore()
    first = store.save(
        Job(type=JobType.BUILD_ALERT, idempotency_key="alert-123")
    )
    second = store.save(
        Job(type=JobType.BUILD_ALERT, idempotency_key="alert-123")
    )
    assert second.id == first.id
    assert store.get_by_idempotency_key("alert-123").id == first.id

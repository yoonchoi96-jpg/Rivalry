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

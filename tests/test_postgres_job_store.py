import os

import pytest

from core.jobs.models import Job, JobStatus, JobType
from core.jobs.postgres_store import PostgresJobStore


@pytest.mark.integration
def test_postgres_job_store_prepare_enqueue_is_idempotent_and_revision_aware():
    dsn = os.getenv("RIVALRY_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("RIVALRY_TEST_DATABASE_URL is not configured")

    from db.migrate import migrate

    migrate(dsn)
    store = PostgresJobStore(dsn)

    key = "postgres-store-regression"
    first = store.prepare_enqueue(Job(
        type=JobType.DISPATCH_ACTION,
        payload={"revision": 1},
        idempotency_key=key,
        enqueue_version=1,
    ))
    duplicate = store.prepare_enqueue(Job(
        type=JobType.DISPATCH_ACTION,
        payload={"revision": 2},
        idempotency_key=key,
        enqueue_version=1,
    ))

    assert duplicate.id == first.id
    assert duplicate.payload == first.payload
    assert duplicate.enqueue_version == first.enqueue_version

    retry = first.model_copy(update={
        "status": JobStatus.QUEUED,
        "payload": {"revision": 2},
        "enqueue_version": first.enqueue_version + 1,
    })
    refreshed = store.prepare_enqueue(retry)
    assert refreshed.id == first.id
    assert refreshed.payload == {"revision": 2}
    assert refreshed.enqueue_version == first.enqueue_version + 1

    pending = [job for job in store.pending_outbox() if job.id == first.id]
    assert len(pending) == 1
    assert pending[0].enqueue_version == first.enqueue_version + 1

    store.mark_outbox_published(first.id, first.enqueue_version)
    assert any(job.id == first.id for job in store.pending_outbox())

    store.mark_outbox_published(first.id, first.enqueue_version + 1)
    assert not any(job.id == first.id for job in store.pending_outbox())

from core.jobs.models import Job, JobStatus, JobType
from core.jobs.queue import InMemoryJobQueue
from core.jobs.worker import JobWorker


def test_worker_retries_then_succeeds():
    queue = InMemoryJobQueue()
    job = Job(type=JobType.BUILD_ALERT, max_attempts=3)
    queue.enqueue(job)
    calls = {"count": 0}

    def flaky(_job):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary")
        return {"ok": True}

    worker = JobWorker(queue, {JobType.BUILD_ALERT: flaky})
    first = worker.run_once()
    assert first.status == JobStatus.QUEUED
    assert first.attempts == 1
    second = worker.run_once()
    assert second.status == JobStatus.SUCCEEDED
    assert second.attempts == 2


def test_worker_marks_terminal_failure_after_max_attempts():
    queue = InMemoryJobQueue()
    job = Job(type=JobType.BUILD_ALERT, max_attempts=2)
    queue.enqueue(job)

    def broken(_job):
        raise RuntimeError("permanent")

    worker = JobWorker(queue, {JobType.BUILD_ALERT: broken})
    worker.run_once()
    final = worker.run_once()
    assert final.status == JobStatus.FAILED
    assert final.attempts == 2
    assert final.error == "permanent"


def test_worker_exponential_backoff_is_recorded():
    queue = InMemoryJobQueue()
    job = Job(type=JobType.BUILD_ALERT, max_attempts=3)
    queue.enqueue(job)
    worker = JobWorker(
        queue,
        {JobType.BUILD_ALERT: lambda _job: (_ for _ in ()).throw(RuntimeError("temporary"))},
        retry_base_seconds=2,
    )
    first = worker.run_once()
    assert first.next_attempt_at is not None
    first_next_attempt_at = first.next_attempt_at
    second = worker.run_once()
    assert second.next_attempt_at is not None
    assert second.next_attempt_at > first_next_attempt_at


def test_worker_claim_prevents_duplicate_execution():
    queue = InMemoryJobQueue()
    job = Job(type=JobType.BUILD_ALERT, max_attempts=3)
    queue.enqueue(job)
    calls = {"count": 0}

    def handler(_job):
        calls["count"] += 1
        return {"ok": True}

    worker_a = JobWorker(queue, {JobType.BUILD_ALERT: handler})
    worker_b = JobWorker(queue, {JobType.BUILD_ALERT: handler})
    first = worker_a.run_once()
    second = worker_b.run_once()
    assert first.status == JobStatus.SUCCEEDED
    assert second is None
    assert calls["count"] == 1


def test_in_memory_claim_is_atomic():
    queue = InMemoryJobQueue()
    job = Job(type=JobType.BUILD_ALERT)
    queue.enqueue(job)
    first = queue.dequeue()
    second = queue.claim(job.id, "2026-10-04T00:00:00+00:00")
    assert first is not None
    assert second is not None
    assert second.status == JobStatus.RUNNING
    assert second.attempts == 1
    assert queue.claim(job.id, "2026-10-04T00:00:01+00:00") is None

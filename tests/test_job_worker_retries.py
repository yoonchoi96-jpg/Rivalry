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

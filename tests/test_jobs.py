from core.jobs.models import Job, JobStatus, JobType
from core.jobs.queue import InMemoryJobQueue
from core.jobs.worker import JobWorker


def test_queue_preserves_job_lifecycle():
    queue = InMemoryJobQueue()
    job = queue.enqueue(Job(type=JobType.COLLECT_COMPETITOR, payload={"competitor_id": "c1"}))
    assert queue.size() == 1
    assert queue.get(job.id).status == JobStatus.QUEUED

    worker = JobWorker(queue, {JobType.COLLECT_COMPETITOR: lambda item: {"collected": item.payload["competitor_id"]}})
    completed = worker.run_once()

    assert completed is not None
    assert completed.status == JobStatus.SUCCEEDED
    assert completed.result == {"collected": "c1"}
    assert completed.started_at is not None
    assert completed.finished_at is not None
    assert queue.size() == 0


def test_queue_deduplicates_idempotent_jobs():
    queue = InMemoryJobQueue()
    first = Job(type=JobType.DISPATCH_ACTION, idempotency_key="action:i1:p1:review")
    second = Job(type=JobType.DISPATCH_ACTION, idempotency_key="action:i1:p1:review")

    stored_first = queue.enqueue(first)
    stored_second = queue.enqueue(second)

    assert stored_second.id == stored_first.id
    assert queue.get(second.id) is None
    assert queue.size() == 1


def test_in_memory_queue_requeues_failed_job():
    queue = InMemoryJobQueue()
    attempts = {"count": 0}

    def handler(_):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return {"ok": True}

    job = queue.enqueue(Job(type=JobType.PROCESS_INTELLIGENCE, max_attempts=2))
    worker = JobWorker(queue, {JobType.PROCESS_INTELLIGENCE: handler}, retry_base_seconds=0)

    first = worker.run_once()
    assert first.status == JobStatus.QUEUED
    assert queue.size() == 1

    second = worker.run_once()
    assert second.status == JobStatus.SUCCEEDED
    assert second.result == {"ok": True}


def test_worker_records_handler_failure():
    queue = InMemoryJobQueue()
    job = queue.enqueue(Job(type=JobType.PROCESS_INTELLIGENCE))
    worker = JobWorker(queue, {JobType.PROCESS_INTELLIGENCE: lambda _: (_ for _ in ()).throw(RuntimeError("boom"))})

    completed = worker.run_once()

    assert completed.status == JobStatus.QUEUED
    assert completed.error == "boom"
    assert completed.finished_at is None
    assert completed.attempts == 1


def test_worker_marks_missing_handler_as_failed():
    queue = InMemoryJobQueue()
    job = queue.enqueue(Job(type=JobType.COLLECT_COMPETITOR))

    completed = JobWorker(queue).run_once()

    assert completed.status == JobStatus.FAILED
    assert "No handler registered" in completed.error
    assert completed.finished_at is not None


def test_research_ingest_follow_up_is_idempotent():
    queue = InMemoryJobQueue()
    worker = JobWorker(queue)
    job = Job(
        type=JobType.INGEST_RESEARCH,
        payload={"business_id": "b1", "policy_id": "p1", "exposure": 0.5},
        result={"observations": [{"id": "obs-1"}]},
        status=JobStatus.SUCCEEDED,
    )

    follow_ups = worker._follow_up_jobs(job)

    assert len(follow_ups) == 1
    assert follow_ups[0].type == JobType.REPROCESS_OBSERVATION
    assert follow_ups[0].idempotency_key == "reprocess:obs-1:p1"

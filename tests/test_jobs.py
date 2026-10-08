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


def test_in_memory_queue_honors_requeue_delay():
    queue = InMemoryJobQueue()
    job = queue.enqueue(Job(type=JobType.PROCESS_INTELLIGENCE))
    queued = queue.dequeue()
    assert queued is not None
    queued.status = JobStatus.QUEUED
    queue.requeue(queued, delay_seconds=60)
    assert queue.dequeue() is None
    assert queue.size() == 1


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


def test_legacy_follow_ups_have_deterministic_idempotency_keys():
    worker = JobWorker(InMemoryJobQueue())
    parent = Job(
        type=JobType.COLLECT_COMPETITOR,
        result={
            "changes": [{"id": "c1"}, {"id": "c2"}],
            "reviews": [{"id": "r1"}],
            "competitor": {"id": "comp-1"},
        },
        status=JobStatus.SUCCEEDED,
    )

    follow_ups = worker._follow_up_jobs(parent)

    assert [job.idempotency_key for job in follow_ups] == [
        f"process-intelligence:{parent.id}:0",
        f"process-intelligence:{parent.id}:1",
        f"analyze-reviews:{parent.id}",
        f"generate-prediction:{parent.id}",
    ]


def test_decision_action_idempotency_is_revision_aware():
    worker = JobWorker(InMemoryJobQueue())
    parent = Job(
        type=JobType.GENERATE_DECISION,
        result={"recommendation": {
            "business_id": "b1", "impact_id": "i1", "action": "review",
            "priority": 0.8, "rationale": "review now", "confidence": 0.9,
            "signal_id": "s1", "factor_key": "competitive_price", "policy_id": "p1",
        }},
        status=JobStatus.SUCCEEDED,
    )
    first = worker._follow_up_jobs(parent)[0]
    revised = parent.model_copy(deep=True)
    revised.result["recommendation"]["rationale"] = "review after verification"
    second = worker._follow_up_jobs(revised)[0]

    assert first.idempotency_key != second.idempotency_key


def test_process_intelligence_follow_up_has_deterministic_idempotency_key():
    worker = JobWorker(InMemoryJobQueue())
    parent = Job(
        type=JobType.PROCESS_INTELLIGENCE,
        payload={"change": {"id": "c1"}},
        result={"score": 1},
        status=JobStatus.SUCCEEDED,
    )

    follow_ups = worker._follow_up_jobs(parent)

    assert len(follow_ups) == 1
    assert follow_ups[0].idempotency_key == f"build-alert:{parent.id}"


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


def test_follow_up_enqueue_failure_keeps_parent_retryable():
    class FailOnceOnSecondFollowUp(InMemoryJobQueue):
        def __init__(self):
            super().__init__()
            self._enqueue_calls = 0

        def enqueue(self, job):
            self._enqueue_calls += 1
            if self._enqueue_calls == 3:
                raise RuntimeError("simulated follow-up enqueue crash")
            return super().enqueue(job)

    queue = FailOnceOnSecondFollowUp()
    parent = queue.enqueue(Job(
        type=JobType.COLLECT_COMPETITOR,
        result={},
        max_attempts=2,
    ))
    # The parent enqueue is call #1. The worker's two children are #2 and #3.
    worker = JobWorker(queue)

    # Supply the successful collection result directly through the handler.
    worker.handlers[JobType.COLLECT_COMPETITOR] = lambda _: {
        "changes": [{"id": "c1"}, {"id": "c2"}],
        "competitor": {"id": "comp-1"},
    }

    completed = worker.run_once()

    assert completed.status == JobStatus.QUEUED
    assert completed.error == "simulated follow-up enqueue crash"
    durable = queue.get(parent.id)
    assert durable is not None
    assert durable.status == JobStatus.QUEUED
    assert queue.size() == 2
    pending = queue.dequeue()
    assert pending is not None
    assert pending.id == parent.id
    child = queue.dequeue()
    assert child is not None
    assert child.idempotency_key == f"process-intelligence:{parent.id}:0"


def test_worker_enqueues_follow_up_before_ack():
    class RecordingQueue(InMemoryJobQueue):
        def __init__(self):
            super().__init__()
            self.ack_seen_with_follow_up = False

        def ack(self, job):
            self.ack_seen_with_follow_up = self.size() > 0
            super().ack(job)

    queue = RecordingQueue()
    queue.enqueue(Job(
        type=JobType.PROCESS_INTELLIGENCE,
        payload={"change": {"id": "change-1"}},
    ))
    worker = JobWorker(
        queue,
        {JobType.PROCESS_INTELLIGENCE: lambda _: {"ok": True}},
    )

    completed = worker.run_once()

    assert completed.status == JobStatus.SUCCEEDED
    assert queue.ack_seen_with_follow_up


def test_decision_action_idempotency_normalizes_action_aliases():
    worker = JobWorker(InMemoryJobQueue())
    base = {
        "business_id": "b1", "impact_id": "i-alias", "priority": 0.8,
        "rationale": "investigate price pressure", "confidence": 0.9,
        "signal_id": "s1", "factor_key": "competitive_price", "policy_id": "p1",
    }
    canonical = Job(
        type=JobType.GENERATE_DECISION,
        result={"recommendation": {**base, "action": "investigate"}},
        status=JobStatus.SUCCEEDED,
    )
    alias = Job(
        type=JobType.GENERATE_DECISION,
        result={"recommendation": {**base, "action": "research"}},
        status=JobStatus.SUCCEEDED,
    )

    first = worker._follow_up_jobs(canonical)[0]
    second = worker._follow_up_jobs(alias)[0]

    assert first.idempotency_key == second.idempotency_key
    assert first.payload["recommendation"]["action"] == "investigate"
    assert second.payload["recommendation"]["action"] == "investigate"

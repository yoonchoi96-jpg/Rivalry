import json

from core.jobs.models import Job, JobType
from core.jobs.redis_queue import RedisJobQueue
from core.jobs.store import InMemoryJobStore


class FakeRedis:
    def __init__(self):
        self.stream = []
        self.dead = []
        self.groups = set()
        self.acked = []
        self.delayed = {}
        self.keys = {}
        self.pending = {}

    def xgroup_create(self, stream, group, id="0", mkstream=False):
        key = (stream, group)
        if key in self.groups:
            raise RuntimeError("BUSYGROUP Consumer Group name already exists")
        self.groups.add(key)

    def set(self, key, value, nx=False):
        if nx and key in self.keys:
            return False
        self.keys[key] = value
        return True

    def xadd(self, stream, fields):
        if stream.endswith(":dead-letter"):
            self.dead.append(fields)
        else:
            self.stream.append((str(len(self.stream) + 1), fields))
        return str(len(self.stream))

    def zadd(self, key, mapping):
        self.delayed.update(mapping)

    def zrangebyscore(self, key, minimum, maximum):
        return [value for value, score in self.delayed.items() if minimum <= score <= maximum]

    def zcard(self, key):
        return len(self.delayed)

    def zrem(self, key, value):
        self.delayed.pop(value, None)

    def xrange(self, stream, count=1000):
        return [(str(i + 1), fields) for i, fields in enumerate(self.dead[:count])]

    def xreadgroup(self, group, consumer, streams, count=1, block=1000):
        if not self.stream:
            return []
        message = self.stream.pop(0)
        self.pending[message[0]] = message
        return [(list(streams)[0], [message])]

    def xautoclaim(self, stream, group, consumer, min_idle_time, start_id="0-0", count=1):
        if not self.pending:
            return ("0-0", [])
        message_id, entry = next(iter(self.pending.items()))
        return ("0-0", [entry])

    def xack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))
        self.pending.pop(message_id, None)

    def eval(self, script, numkeys, marker, stream, raw):
        if marker in self.keys:
            return "0-0"
        self.keys[marker] = "1"
        return self.xadd(stream, {"job": raw})

    def xlen(self, stream):
        if stream.endswith(":dead-letter"):
            return len(self.dead)
        return len(self.stream)


def test_redis_queue_shares_state_through_job_store():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = Job(type=JobType.COLLECT_COMPETITOR)
    queue.enqueue(job)
    fetched = queue.get(job.id)
    assert fetched is not None
    assert fetched.id == job.id
    dequeued = queue.dequeue()
    assert dequeued is not None
    assert dequeued.id == job.id
    dequeued.attempts += 1
    queue.update(dequeued)
    assert queue.get(job.id).attempts == 1


def test_dead_letter_acknowledges_message():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = Job(type=JobType.COLLECT_COMPETITOR)
    queue.enqueue(job)
    dequeued = queue.dequeue()
    queue.dead_letter(dequeued, "boom")
    assert len(redis.dead) == 1
    assert redis.acked


def test_delayed_requeue_and_dlq_replay(monkeypatch):
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = Job(type=JobType.BUILD_ALERT)
    queue.enqueue(job)
    dequeued = queue.dequeue()
    queue.requeue(dequeued, delay_seconds=10)
    assert queue.dequeue() is None

    queue.dead_letter(dequeued, "boom")
    replayed = queue.replay_dead_letter(job.id)
    assert replayed is not None
    assert replayed.status.value == "queued"


def test_redis_queue_deduplicates_idempotency_key():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    first = queue.enqueue(Job(type=JobType.BUILD_ALERT, idempotency_key="alert-123"))
    second = queue.enqueue(Job(type=JobType.BUILD_ALERT, idempotency_key="alert-123"))
    assert second.id == first.id
    assert len(redis.stream) == 1


def test_idempotent_job_immediate_requeue_is_enqueued_again():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = queue.enqueue(Job(type=JobType.BUILD_ALERT, idempotency_key="retry-123"))
    dequeued = queue.dequeue()
    queue.requeue(dequeued)
    assert len(redis.stream) == 1
    assert queue.dequeue().id == job.id


def test_idempotent_delayed_requeue_is_promoted(monkeypatch):
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = queue.enqueue(Job(type=JobType.BUILD_ALERT, idempotency_key="delay-123"))
    dequeued = queue.dequeue()
    monkeypatch.setattr("core.jobs.redis_queue.time.time", lambda: 100.0)
    queue.requeue(dequeued, delay_seconds=10)
    monkeypatch.setattr("core.jobs.redis_queue.time.time", lambda: 111.0)
    promoted = queue.dequeue()
    assert promoted is not None
    assert promoted.id == job.id


def test_idempotent_dlq_replay_is_enqueued():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = queue.enqueue(Job(type=JobType.BUILD_ALERT, idempotency_key="dlq-123"))
    dequeued = queue.dequeue()
    queue.dead_letter(dequeued, "boom")
    assert not redis.stream
    replayed = queue.replay_dead_letter(job.id)
    assert replayed is not None
    assert queue.dequeue().id == job.id


def test_queue_metrics_expose_stream_pending_delayed_and_dlq():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = queue.enqueue(Job(type=JobType.BUILD_ALERT))
    assert queue.metrics()["stream_total"] == 1
    assert queue.metrics()["pending"] == 0
    assert queue.metrics()["delayed"] == 0
    assert queue.metrics()["dead_letter"] == 0
    dequeued = queue.dequeue()
    queue.requeue(dequeued, delay_seconds=10)
    assert queue.metrics()["delayed"] == 1


def test_outbox_reconciliation_publishes_pending_job_once():
    store = InMemoryJobStore()
    redis = FakeRedis()
    queue = RedisJobQueue("redis://unused", job_store=store, client=redis)
    job = Job(type=JobType.BUILD_ALERT)
    job.enqueue_version = 1
    store.prepare_enqueue(job)
    assert queue.reconcile_outbox() == 1
    assert queue.reconcile_outbox() == 0
    assert len(redis.stream) == 1



def test_xautoclaim_reclaims_pending_message_after_consumer_crash():
    store = InMemoryJobStore()
    redis = FakeRedis()
    first = RedisJobQueue(
        "redis://unused", job_store=store, client=redis, consumer="worker-a", reclaim_after_ms=1
    )
    job = first.enqueue(Job(type=JobType.BUILD_ALERT))
    dequeued = first.dequeue()
    assert dequeued is not None
    second = RedisJobQueue(
        "redis://unused", job_store=store, client=redis, consumer="worker-b", reclaim_after_ms=1
    )
    reclaimed = second.dequeue()
    assert reclaimed is not None
    assert reclaimed.id == job.id
    second.ack(reclaimed)
    assert not redis.pending

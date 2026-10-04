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

    def zrem(self, key, value):
        self.delayed.pop(value, None)

    def xrange(self, stream, count=1000):
        return [(str(i + 1), fields) for i, fields in enumerate(self.dead[:count])]

    def xreadgroup(self, group, consumer, streams, count=1, block=1000):
        if not self.stream:
            return []
        return [(list(streams)[0], [self.stream.pop(0)])]

    def xack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))

    def xlen(self, stream):
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

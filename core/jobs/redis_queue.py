from __future__ import annotations

import json
import time
from typing import Any

from .models import Job, JobStatus
from .store import JobStore


class RedisJobQueue:
    """Durable cross-process queue backed by Redis Streams and a job store."""

    def __init__(
        self,
        url: str,
        *,
        job_store: JobStore,
        stream: str = "rivalry:jobs",
        group: str = "rivalry-workers",
        consumer: str = "worker",
        client: Any | None = None,
        reclaim_after_ms: int = 60_000,
    ) -> None:
        if not url and client is None:
            raise ValueError("Redis URL must not be empty")
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("redis package is required for RedisJobQueue") from exc
        self.client = client or redis.Redis.from_url(url, decode_responses=True)
        self.job_store = job_store
        self.stream = stream
        self.group = group
        self.consumer = consumer
        self.reclaim_after_ms = reclaim_after_ms
        self.delayed_key = f"{stream}:delayed"
        self.dead_letter_stream = f"{stream}:dead-letter"
        self.idempotency_prefix = f"{stream}:idempotency:"
        self._message_ids: dict[str, str] = {}
        self._publish_script = """
        local created = redis.call("SET", KEYS[1], "1", "NX")
        if created then
            return redis.call("XADD", KEYS[2], "*", "job", ARGV[1])
        end
        return "0-0"
        """
        self._ensure_group()

    def _ensure_group(self) -> None:
        try:
            self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def _publish(self, job: Job) -> None:
        raw = json.dumps(job.model_dump(mode="json"), sort_keys=True)
        marker = f"{self.idempotency_prefix}published:{job.id}:{job.enqueue_version}"
        eval_script = getattr(self.client, "eval", None)
        if callable(eval_script):
            eval_script(self._publish_script, 2, marker, self.stream, raw)
        else:
            self.client.xadd(self.stream, {"job": raw})

    def _enqueue_existing(self, job: Job) -> Job:
        job.status = JobStatus.QUEUED
        job.next_attempt_at = None
        job.enqueue_version += 1
        prepare = getattr(self.job_store, "prepare_enqueue", None)
        canonical = prepare(job) if callable(prepare) else self.job_store.save(job)
        self._publish(canonical)
        mark = getattr(self.job_store, "mark_outbox_published", None)
        if callable(mark):
            mark(canonical.id, canonical.enqueue_version)
        return self.job_store.get(canonical.id) or canonical

    def reconcile_outbox(self, limit: int = 100) -> int:
        pending = getattr(self.job_store, "pending_outbox", None)
        if not callable(pending):
            return 0
        published = 0
        for job in pending(limit):
            try:
                self._publish(job)
                mark = getattr(self.job_store, "mark_outbox_published", None)
                if callable(mark):
                    mark(job.id, job.enqueue_version)
                published += 1
            except Exception:
                continue
        return published

    def enqueue(self, job: Job) -> Job:
        # PostgreSQL/InMemory job state is the idempotency authority. Do not
        # claim a Redis-only marker before durable preparation: a crash in
        # that gap could permanently suppress the job from the outbox.
        if job.idempotency_key:
            existing = self.job_store.get_by_idempotency_key(job.idempotency_key)
            if existing is not None and existing.id != job.id:
                return existing
        return self._enqueue_existing(job)

    def _decode_entry(self, entry: tuple[str, dict[str, str]]) -> Job | None:
        message_id, fields = entry
        queued_job = Job.model_validate(json.loads(fields["job"]))
        current_job = self.job_store.get(queued_job.id)

        # Requeue/retry creates a newer enqueue_version while the original
        # Redis Streams delivery may remain pending. Never execute stale
        # deliveries: acknowledge them and let the newer entry win.
        if current_job is not None and queued_job.enqueue_version < current_job.enqueue_version:
            self.client.xack(self.stream, self.group, message_id)
            return None

        self._message_ids[queued_job.id] = message_id
        return current_job or queued_job

    def _promote_due(self) -> None:
        now = time.time()
        due = self.client.zrangebyscore(self.delayed_key, 0, now)
        for raw in due:
            job = Job.model_validate(json.loads(raw))
            self.client.zrem(self.delayed_key, raw)
            self._enqueue_existing(job)

    def dequeue(self) -> Job | None:
        self.reconcile_outbox()
        self._promote_due()

        xautoclaim = getattr(self.client, "xautoclaim", None)
        if callable(xautoclaim):
            claimed = xautoclaim(
                self.stream,
                self.group,
                self.consumer,
                min_idle_time=self.reclaim_after_ms,
                start_id="0-0",
                count=1,
            )
            entries = claimed[1] if isinstance(claimed, tuple) else []
            if entries:
                job = self._decode_entry(entries[0])
                if job is not None:
                    return job

        # A stale entry may be encountered first. Keep reading until a
        # current delivery is found rather than exposing the stale message.
        while True:
            messages = self.client.xreadgroup(
                self.group,
                self.consumer,
                {self.stream: ">"},
                count=1,
                block=1000,
            )
            if not messages:
                return None
            _, entries = messages[0]
            job = self._decode_entry(entries[0])
            if job is not None:
                return job

    def get(self, job_id: str) -> Job | None:
        return self.job_store.get(job_id)

    def update(self, job: Job) -> Job:
        return self.job_store.save(job)

    def ack(self, job: Job) -> None:
        message_id = self._message_ids.pop(job.id, None)
        if message_id:
            self.client.xack(self.stream, self.group, message_id)

    def dead_letter(self, job: Job, reason: str) -> None:
        self.client.xadd(
            self.dead_letter_stream,
            {"job": json.dumps(job.model_dump(mode="json")), "reason": reason},
        )
        self.ack(job)

    def replay_dead_letter(self, job_id: str) -> Job | None:
        entries = self.client.xrange(self.dead_letter_stream, count=1000)
        for _, fields in entries:
            raw = fields.get("job")
            if not raw:
                continue
            job = Job.model_validate(json.loads(raw))
            if job.id == job_id:
                job.status = JobStatus.QUEUED
                job.error = None
                job.finished_at = None
                job.next_attempt_at = None
                self._enqueue_existing(job)
                return job
        return None

    def requeue(self, job: Job, *, delay_seconds: float = 0) -> Job:
        if delay_seconds <= 0:
            self.ack(job)
            return self._enqueue_existing(job)
        job.status = JobStatus.QUEUED
        job.enqueue_version += 1
        self.job_store.save(job)
        self.client.zadd(
            self.delayed_key,
            {json.dumps(job.model_dump(mode="json"), sort_keys=True): time.time() + delay_seconds},
        )
        return job

    def metrics(self) -> dict[str, int]:
        """Return Redis-backed queue state metrics for operational monitoring."""
        pending = 0
        xpending = getattr(self.client, "xpending", None)
        if callable(xpending):
            summary = xpending(self.stream, self.group)
            if isinstance(summary, dict):
                pending = int(summary.get("pending", 0))
            elif isinstance(summary, (tuple, list)) and summary:
                pending = int(summary[0])
        zcard = getattr(self.client, "zcard", None)
        delayed = int(zcard(self.delayed_key)) if callable(zcard) else 0
        return {
            "stream_total": int(self.client.xlen(self.stream)),
            "pending": pending,
            "delayed": delayed,
            "dead_letter": int(self.client.xlen(self.dead_letter_stream)),
        }

    def size(self) -> int:
        return int(self.client.xlen(self.stream))

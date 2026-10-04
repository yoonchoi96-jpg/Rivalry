from __future__ import annotations

import json
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
        self._message_ids: dict[str, str] = {}
        self._ensure_group()

    def _ensure_group(self) -> None:
        try:
            self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def enqueue(self, job: Job) -> Job:
        job.status = JobStatus.QUEUED
        self.job_store.save(job)
        self.client.xadd(self.stream, {"job": json.dumps(job.model_dump(mode="json"))})
        return self.job_store.get(job.id) or job

    def dequeue(self) -> Job | None:
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
        message_id, fields = entries[0]
        job = Job.model_validate(json.loads(fields["job"]))
        self._message_ids[job.id] = message_id
        return self.job_store.get(job.id) or job

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
            f"{self.stream}:dead-letter",
            {"job": json.dumps(job.model_dump(mode="json")), "reason": reason},
        )
        self.ack(job)

    def requeue(self, job: Job) -> Job:
        self.ack(job)
        return self.enqueue(job)

    def size(self) -> int:
        return int(self.client.xlen(self.stream))

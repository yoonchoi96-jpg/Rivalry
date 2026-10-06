from __future__ import annotations

from collections import deque
from threading import Lock
import time
from typing import Protocol

from .models import Job, JobStatus


class JobQueue(Protocol):
    def enqueue(self, job: Job) -> Job: ...
    def dequeue(self) -> Job | None: ...
    def get(self, job_id: str) -> Job | None: ...
    def update(self, job: Job) -> Job: ...
    def requeue(self, job: Job, *, delay_seconds: float = 0) -> Job: ...


class InMemoryJobQueue:
    """Small queue seam for the MVP; mirrors durable idempotent enqueue semantics."""

    def __init__(self) -> None:
        self._pending: deque[str] = deque()
        self._jobs: dict[str, Job] = {}
        self._idempotency: dict[str, str] = {}
        self._not_before: dict[str, float] = {}
        self._lock = Lock()

    def enqueue(self, job: Job) -> Job:
        with self._lock:
            if job.idempotency_key:
                existing_id = self._idempotency.get(job.idempotency_key)
                if existing_id:
                    existing = self._jobs.get(existing_id)
                    if existing is not None:
                        return existing
                self._idempotency[job.idempotency_key] = job.id
            self._jobs[job.id] = job
            self._pending.append(job.id)
            return job

    def dequeue(self) -> Job | None:
        with self._lock:
            now = time.monotonic()
            for _ in range(len(self._pending)):
                job_id = self._pending.popleft()
                job = self._jobs.get(job_id)
                if job is None or job.status != JobStatus.QUEUED:
                    self._not_before.pop(job_id, None)
                    continue
                due = self._not_before.get(job_id, 0.0)
                if due > now:
                    self._pending.append(job_id)
                    continue
                self._not_before.pop(job_id, None)
                return job
            return None

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
            if job.idempotency_key:
                self._idempotency[job.idempotency_key] = job.id
            return job

    def requeue(self, job: Job, *, delay_seconds: float = 0) -> Job:
        with self._lock:
            self._jobs[job.id] = job
            self._not_before[job.id] = time.monotonic() + max(0.0, delay_seconds)
            self._pending.append(job.id)
            return job

    def size(self) -> int:
        with self._lock:
            return sum(1 for job in self._jobs.values() if job.status == JobStatus.QUEUED)

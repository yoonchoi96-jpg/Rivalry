from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Protocol

from .models import Job, JobStatus


class JobQueue(Protocol):
    def enqueue(self, job: Job) -> Job: ...
    def dequeue(self) -> Job | None: ...
    def get(self, job_id: str) -> Job | None: ...
    def update(self, job: Job) -> Job: ...


class InMemoryJobQueue:
    """Small queue seam for the MVP; mirrors durable idempotent enqueue semantics."""

    def __init__(self) -> None:
        self._pending: deque[str] = deque()
        self._jobs: dict[str, Job] = {}
        self._idempotency: dict[str, str] = {}
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
            while self._pending:
                job_id = self._pending.popleft()
                job = self._jobs.get(job_id)
                if job is not None and job.status == JobStatus.QUEUED:
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

    def size(self) -> int:
        with self._lock:
            return sum(1 for job in self._jobs.values() if job.status == JobStatus.QUEUED)

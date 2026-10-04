from __future__ import annotations

from threading import Lock
from typing import Protocol

from .models import Job


class JobStore(Protocol):
    def save(self, job: Job) -> Job: ...
    def get(self, job_id: str) -> Job | None: ...
    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None: ...
    def prepare_enqueue(self, job: Job) -> Job: ...
    def pending_outbox(self, limit: int = 100) -> list[Job]: ...
    def mark_outbox_published(self, job_id: str, enqueue_version: int) -> None: ...
    def claim(self, job_id: str, started_at: str) -> Job | None: ...


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()
        self._outbox: dict[str, int] = {}

    def save(self, job: Job) -> Job:
        with self._lock:
            if job.idempotency_key:
                for existing in self._jobs.values():
                    if (
                        existing.idempotency_key == job.idempotency_key
                        and existing.id != job.id
                    ):
                        return Job.model_validate(existing.model_dump(mode="json"))
            self._jobs[job.id] = Job.model_validate(job.model_dump(mode="json"))
            return Job.model_validate(job.model_dump(mode="json"))

    def prepare_enqueue(self, job: Job) -> Job:
        with self._lock:
            if job.idempotency_key:
                for existing in self._jobs.values():
                    if existing.idempotency_key == job.idempotency_key and existing.id != job.id:
                        return Job.model_validate(existing.model_dump(mode="json"))
            canonical = Job.model_validate(job.model_dump(mode="json"))
            self._jobs[canonical.id] = canonical
            self._outbox[canonical.id] = canonical.enqueue_version
            return Job.model_validate(canonical.model_dump(mode="json"))

    def pending_outbox(self, limit: int = 100) -> list[Job]:
        with self._lock:
            ids = list(self._outbox)[:limit]
            return [
                Job.model_validate(self._jobs[job_id].model_dump(mode="json"))
                for job_id in ids
                if job_id in self._jobs
            ]

    def mark_outbox_published(self, job_id: str, enqueue_version: int) -> None:
        with self._lock:
            if self._outbox.get(job_id) == enqueue_version:
                self._outbox.pop(job_id, None)

    def claim(self, job_id: str, started_at: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status != "queued":
                return None
            job = Job.model_validate(job.model_dump(mode="json"))
            job.status = "running"
            job.started_at = started_at
            job.finished_at = None
            job.next_attempt_at = None
            job.attempts += 1
            self._jobs[job.id] = job
            return Job.model_validate(job.model_dump(mode="json"))

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return Job.model_validate(job.model_dump(mode="json")) if job else None

    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        with self._lock:
            for job in self._jobs.values():
                if job.idempotency_key == idempotency_key:
                    return Job.model_validate(job.model_dump(mode="json"))
            return None

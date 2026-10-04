from __future__ import annotations

from threading import Lock
from typing import Protocol

from .models import Job


class JobStore(Protocol):
    def save(self, job: Job) -> Job: ...
    def get(self, job_id: str) -> Job | None: ...
    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None: ...


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

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

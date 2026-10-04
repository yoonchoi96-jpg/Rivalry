from __future__ import annotations

from threading import Lock
from typing import Protocol

from .models import Job


class JobStore(Protocol):
    def save(self, job: Job) -> Job: ...
    def get(self, job_id: str) -> Job | None: ...


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def save(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = Job.model_validate(job.model_dump(mode="json"))
            return Job.model_validate(job.model_dump(mode="json"))

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return Job.model_validate(job.model_dump(mode="json")) if job else None

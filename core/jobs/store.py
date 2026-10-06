from __future__ import annotations

from datetime import datetime, timezone
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
    def count_scheduled(self) -> int: ...


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
            now = datetime.now(timezone.utc)
            result: list[Job] = []
            for job_id in self._outbox:
                if len(result) >= limit:
                    break
                job = self._jobs.get(job_id)
                if job is None:
                    continue
                if job.next_attempt_at:
                    due = datetime.fromisoformat(job.next_attempt_at)
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=timezone.utc)
                    if due > now:
                        continue
                result.append(Job.model_validate(job.model_dump(mode="json")))
            return result

    def mark_outbox_published(self, job_id: str, enqueue_version: int) -> None:
        with self._lock:
            if self._outbox.get(job_id) == enqueue_version:
                self._outbox.pop(job_id, None)

    def count_scheduled(self) -> int:
        with self._lock:
            now = datetime.now(timezone.utc)
            return sum(
                1
                for job_id in self._outbox
                if job_id in self._jobs
                and self._jobs[job_id].next_attempt_at
                and datetime.fromisoformat(self._jobs[job_id].next_attempt_at) > now
            )

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

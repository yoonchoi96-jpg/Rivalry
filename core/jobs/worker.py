from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .models import Job, JobStatus, JobType
from .queue import InMemoryJobQueue

JobHandler = Callable[[Job], dict[str, object] | None]


class JobWorker:
    """Dispatch queued jobs and optionally enqueue deterministic follow-up jobs."""

    def __init__(self, queue: InMemoryJobQueue, handlers: dict[JobType, JobHandler] | None = None) -> None:
        self.queue = queue
        self.handlers = handlers or {}

    def _follow_up_jobs(self, job: Job) -> list[Job]:
        if job.status != JobStatus.SUCCEEDED or not job.result:
            return []
        if job.type == JobType.COLLECT_COMPETITOR:
            changes = job.result.get("changes", [])
            if not isinstance(changes, list):
                return []
            return [Job(type=JobType.PROCESS_INTELLIGENCE, payload={"change": change}) for change in changes if isinstance(change, dict)]
        if job.type == JobType.PROCESS_INTELLIGENCE:
            change = job.payload.get("change")
            if isinstance(change, dict):
                return [Job(type=JobType.BUILD_ALERT, payload={"change": change, "intelligence": job.result})]
        return []

    def run_once(self) -> Job | None:
        job = self.queue.dequeue()
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc).isoformat()
        self.queue.update(job)
        try:
            handler = self.handlers.get(job.type)
            if handler is None:
                raise ValueError(f"No handler registered for job type: {job.type.value}")
            job.result = handler(job) or {}
            job.status = JobStatus.SUCCEEDED
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
        finally:
            job.finished_at = datetime.now(timezone.utc).isoformat()
            self.queue.update(job)
        for follow_up in self._follow_up_jobs(job):
            self.queue.enqueue(follow_up)
        return job

    def drain(self, limit: int | None = None) -> list[Job]:
        completed: list[Job] = []
        while limit is None or len(completed) < limit:
            job = self.run_once()
            if job is None:
                break
            completed.append(job)
        return completed

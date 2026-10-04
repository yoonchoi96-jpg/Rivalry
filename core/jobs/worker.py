from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .models import Job, JobStatus, JobType
from .queue import JobQueue

JobHandler = Callable[[Job], dict[str, object] | None]


class JobWorker:
    """Dispatch jobs, retry transient failures, and enqueue deterministic follow-ups."""

    def __init__(self, queue: JobQueue, handlers: dict[JobType, JobHandler] | None = None) -> None:
        self.queue = queue
        self.handlers = handlers or {}

    def _follow_up_jobs(self, job: Job) -> list[Job]:
        if job.status != JobStatus.SUCCEEDED or not job.result:
            return []
        if job.type == JobType.COLLECT_COMPETITOR:
            changes = job.result.get("changes", [])
            if not isinstance(changes, list):
                return []
            jobs = [
                Job(type=JobType.PROCESS_INTELLIGENCE, payload={"change": change})
                for change in changes
                if isinstance(change, dict)
            ]
            reviews = job.result.get("reviews", [])
            competitor = job.result.get("competitor", {})
            if isinstance(reviews, list) and reviews and isinstance(competitor, dict):
                jobs.append(Job(type=JobType.ANALYZE_REVIEWS, payload={"reviews": reviews, "days": 3}))
            if changes and isinstance(competitor, dict) and competitor.get("id"):
                jobs.append(Job(
                    type=JobType.GENERATE_PREDICTION,
                    payload={"competitor_id": competitor["id"], "changes": changes},
                ))
            return jobs
        if job.type == JobType.PROCESS_INTELLIGENCE:
            change = job.payload.get("change")
            if isinstance(change, dict):
                return [Job(
                    type=JobType.BUILD_ALERT,
                    payload={"change": change, "intelligence": job.result},
                )]
        return []

    def _ack(self, job: Job) -> None:
        ack = getattr(self.queue, "ack", None)
        if callable(ack):
            ack(job)

    def _dead_letter(self, job: Job) -> None:
        dead_letter = getattr(self.queue, "dead_letter", None)
        if callable(dead_letter):
            dead_letter(job, job.error or "job failed")
        else:
            self._ack(job)

    def _retry(self, job: Job) -> None:
        job.status = JobStatus.QUEUED
        job.finished_at = None
        self.queue.update(job)
        requeue = getattr(self.queue, "requeue", None)
        if callable(requeue):
            requeue(job)
        else:
            self.queue.enqueue(job)

    def run_once(self) -> Job | None:
        job = self.queue.dequeue()
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc).isoformat()
        job.finished_at = None
        job.attempts += 1
        self.queue.update(job)
        try:
            handler = self.handlers.get(job.type)
            if handler is None:
                raise ValueError(f"No handler registered for job type: {job.type.value}")
            job.result = handler(job) or {}
            job.status = JobStatus.SUCCEEDED
            job.error = None
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
        finally:
            if job.status == JobStatus.SUCCEEDED:
                job.finished_at = datetime.now(timezone.utc).isoformat()
                self.queue.update(job)
                self._ack(job)
            elif job.attempts < job.max_attempts:
                self._retry(job)
            else:
                job.finished_at = datetime.now(timezone.utc).isoformat()
                self.queue.update(job)
                self._dead_letter(job)
        if job.status == JobStatus.SUCCEEDED:
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

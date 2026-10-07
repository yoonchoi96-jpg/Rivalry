from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Callable

from .models import Job, JobStatus, JobType
from .queue import JobQueue

JobHandler = Callable[[Job], dict[str, object] | None]


class JobWorker:
    """Dispatch jobs, retry transient failures, and enqueue deterministic follow-ups."""

    def __init__(
        self,
        queue: JobQueue,
        handlers: dict[JobType, JobHandler] | None = None,
        *,
        retry_base_seconds: float = 2.0,
        retry_max_seconds: float = 60.0,
    ) -> None:
        self.queue = queue
        self.handlers = handlers or {}
        self.retry_base_seconds = retry_base_seconds
        self.retry_max_seconds = retry_max_seconds

    def _follow_up_jobs(self, job: Job) -> list[Job]:
        if job.status != JobStatus.SUCCEEDED or not job.result:
            return []
        if job.type == JobType.COLLECT_COMPETITOR:
            changes = job.result.get("changes", [])
            if not isinstance(changes, list):
                return []
            jobs = [
                Job(
                    type=JobType.PROCESS_INTELLIGENCE,
                    payload={"change": change},
                    idempotency_key=f"process-intelligence:{job.id}:{index}",
                )
                for index, change in enumerate(changes)
                if isinstance(change, dict)
            ]
            reviews = job.result.get("reviews", [])
            competitor = job.result.get("competitor", {})
            if isinstance(reviews, list) and reviews and isinstance(competitor, dict):
                jobs.append(Job(
                    type=JobType.ANALYZE_REVIEWS,
                    payload={"reviews": reviews, "days": 3},
                    idempotency_key=f"analyze-reviews:{job.id}",
                ))
            if changes and isinstance(competitor, dict) and competitor.get("id"):
                jobs.append(Job(
                    type=JobType.GENERATE_PREDICTION,
                    payload={"competitor_id": competitor["id"], "changes": changes},
                    idempotency_key=f"generate-prediction:{job.id}",
                ))
            return jobs
        if job.type == JobType.GENERATE_DECISION:
            recommendation = job.result.get("recommendation")
            if isinstance(recommendation, dict):
                # Canonicalize policy aliases before deriving the action job identity.
                # This keeps alias-equivalent recommendations idempotent end-to-end.
                from core.action.dispatcher import ActionDispatcher
                from core.decision.models import DecisionRecommendation

                typed_recommendation = DecisionRecommendation.model_validate(recommendation)
                canonical_action = ActionDispatcher().dispatch(typed_recommendation).action
                canonical_recommendation = typed_recommendation.model_copy(
                    update={"action": canonical_action}
                ).model_dump(mode="json")
                revision = sha256(
                    json.dumps(
                        canonical_recommendation,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()[:16]
                return [Job(
                    type=JobType.DISPATCH_ACTION,
                    payload={"recommendation": canonical_recommendation},
                    idempotency_key=f"action:{canonical_recommendation.get('impact_id', job.id)}:{revision}",
                )]
        if job.type == JobType.DISPATCH_ACTION:
            action = job.result.get("action")
            if isinstance(action, dict):
                follow_up_job = action.get("follow_up_job")
                payload = action.get("follow_up_payload")
                if isinstance(follow_up_job, str) and isinstance(payload, dict):
                    revision = sha256(
                        json.dumps(action, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest()[:16]
                    return [Job(
                        type=JobType(follow_up_job),
                        payload=payload,
                        idempotency_key=f"followup:{action.get('recommendation_id', job.id)}:{revision}:{follow_up_job}",
                    )]
        if job.type == JobType.EXECUTE_RESEARCH:
            return [Job(
                type=JobType.INGEST_RESEARCH,
                payload={"research": job.result, "business_id": job.payload.get("business_id"), "policy_id": job.payload.get("policy_id"), "exposure": job.payload.get("exposure", 0.5)},
                idempotency_key=f"ingest-research:{job.id}",
            )]
        if job.type == JobType.INGEST_RESEARCH:
            observations = job.result.get("observations", [])
            return [Job(type=JobType.REPROCESS_OBSERVATION, payload={"observation": item, "business_id": job.payload.get("business_id"), "policy_id": job.payload.get("policy_id"), "exposure": job.payload.get("exposure", 0.5)}, idempotency_key=f"reprocess:{item.get('id', job.id)}:{job.payload.get('policy_id', 'default')}") for item in observations if isinstance(item, dict)]
        if job.type == JobType.REPROCESS_OBSERVATION:
            impact = job.result.get("impact")
            policy_id = job.result.get("policy_id")
            if isinstance(impact, dict) and isinstance(policy_id, str) and policy_id:
                return [Job(type=JobType.GENERATE_DECISION, payload={"impact_id": impact.get("id"), "policy_id": policy_id}, idempotency_key=f"research-decision:{impact.get('id')}:{policy_id}")]
            return []
        if job.type == JobType.PROCESS_INTELLIGENCE:
            change = job.payload.get("change")
            if isinstance(change, dict):
                return [Job(
                    type=JobType.BUILD_ALERT,
                    payload={"change": change, "intelligence": job.result},
                    idempotency_key=f"build-alert:{job.id}",
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

    def _retry_delay(self, job: Job) -> float:
        return min(self.retry_max_seconds, self.retry_base_seconds * (2 ** max(job.attempts - 1, 0)))

    def _retry(self, job: Job) -> None:
        delay = self._retry_delay(job)
        job.status = JobStatus.QUEUED
        job.finished_at = None
        job.next_attempt_at = (
            datetime.now(timezone.utc) + timedelta(seconds=delay)
        ).isoformat()
        requeue = getattr(self.queue, "requeue", None)
        if callable(requeue):
            try:
                requeue(job, delay_seconds=delay)
            except TypeError:
                requeue(job)
        else:
            self.queue.update(job)
            self.queue.enqueue(job)

    def run_once(self) -> Job | None:
        job = self.queue.dequeue()
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc).isoformat()
        job.finished_at = None
        job.next_attempt_at = None
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
                for follow_up in self._follow_up_jobs(job):
                    self.queue.enqueue(follow_up)
                self._ack(job)
            elif job.error and job.error.startswith("No handler registered"):
                job.finished_at = datetime.now(timezone.utc).isoformat()
                self.queue.update(job)
                self._dead_letter(job)
            elif job.attempts < job.max_attempts:
                self._retry(job)
            else:
                job.finished_at = datetime.now(timezone.utc).isoformat()
                job.next_attempt_at = None
                self.queue.update(job)
                self._dead_letter(job)
        return job

    def drain(self, limit: int | None = None) -> list[Job]:
        completed: list[Job] = []
        while limit is None or len(completed) < limit:
            job = self.run_once()
            if job is None:
                break
            completed.append(job)
        return completed

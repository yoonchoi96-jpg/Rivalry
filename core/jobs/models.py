from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobType(StrEnum):
    COLLECT_COMPETITOR = "collect_competitor"
    PROCESS_INTELLIGENCE = "process_intelligence"


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: JobType
    payload: dict[str, object] = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result: dict[str, object] | None = None

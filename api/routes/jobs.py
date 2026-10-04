from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.jobs.models import Job, JobType
from core.jobs.queue import InMemoryJobQueue

router = APIRouter(prefix="/jobs", tags=["jobs"])
queue = InMemoryJobQueue()


class JobCreateRequest(BaseModel):
    type: JobType
    payload: dict[str, object] = Field(default_factory=dict)


@router.post("", response_model=Job, status_code=202)
def enqueue_job(request: JobCreateRequest) -> Job:
    return queue.enqueue(Job(type=request.type, payload=request.payload))


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    job = queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

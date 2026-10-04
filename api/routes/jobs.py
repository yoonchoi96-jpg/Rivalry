from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.jobs.models import Job, JobType
from core.jobs.runtime import job_queue

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreateRequest(BaseModel):
    type: JobType
    payload: dict[str, object] = Field(default_factory=dict)


@router.post("", response_model=Job, status_code=202)
def enqueue_job(request: JobCreateRequest) -> Job:
    return job_queue.enqueue(Job(type=request.type, payload=request.payload))


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    job = job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

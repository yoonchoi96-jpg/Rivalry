from fastapi.testclient import TestClient

from api.main import app
from api.routes import jobs as jobs_route
from core.jobs.models import Job, JobType
from core.jobs.store import InMemoryJobStore


def test_get_job_reads_shared_job_store():
    store = InMemoryJobStore()
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"competitor_id": "c1"})
    store.save(job)

    original_store = jobs_route.job_store
    try:
        jobs_route.job_store = store
        response = TestClient(app).get(f"/api/v1/jobs/{job.id}")
    finally:
        jobs_route.job_store = original_store

    assert response.status_code == 200
    assert response.json()["id"] == job.id
    assert response.json()["payload"] == {"competitor_id": "c1"}


def test_get_job_returns_404_when_store_has_no_job():
    store = InMemoryJobStore()
    original_store = jobs_route.job_store
    try:
        jobs_route.job_store = store
        response = TestClient(app).get("/api/v1/jobs/missing")
    finally:
        jobs_route.job_store = original_store

    assert response.status_code == 404

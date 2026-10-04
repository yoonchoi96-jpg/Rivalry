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


def test_enqueue_job_accepts_idempotency_key():
    store = InMemoryJobStore()

    class Queue:
        def enqueue(self, job):
            return store.save(job)

    original_queue = jobs_route.job_queue
    try:
        jobs_route.job_queue = Queue()
        client = TestClient(app)
        payload = {
            "type": JobType.BUILD_ALERT.value,
            "payload": {"competitor_id": "c1"},
            "idempotency_key": "alert-123",
        }
        first = client.post("/api/v1/jobs", json=payload)
        second = client.post("/api/v1/jobs", json=payload)
    finally:
        jobs_route.job_queue = original_queue

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]

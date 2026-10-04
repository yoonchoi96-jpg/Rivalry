from core.jobs.runtime import job_queue
from core.jobs.worker import JobWorker


# Worker entrypoint. Production deployment can run this module separately from the API.
worker = JobWorker(job_queue)


if __name__ == "__main__":
    worker.drain()

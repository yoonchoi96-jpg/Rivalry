from core.jobs.handlers import JobHandlers
from core.jobs.runtime import intelligence_store, job_queue
from core.jobs.worker import JobWorker


handlers = JobHandlers(store=intelligence_store)
worker = JobWorker(job_queue, handlers.registry())


if __name__ == "__main__":
    worker.drain()

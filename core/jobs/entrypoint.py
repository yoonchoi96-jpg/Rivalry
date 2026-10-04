from __future__ import annotations

import logging
import os
import signal
import time

from .handlers import JobHandlers
from .runtime import intelligence_store, job_queue
from .worker import JobWorker

logger = logging.getLogger(__name__)


def run_worker(*, poll_interval: float | None = None) -> None:
    """Run a long-lived worker process against the shared durable runtime."""
    interval = poll_interval if poll_interval is not None else float(
        os.getenv("RIVALRY_WORKER_POLL_INTERVAL", "1.0")
    )
    stopping = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    handlers = JobHandlers(store=intelligence_store).registry()
    worker = JobWorker(job_queue, handlers=handlers)
    logger.info("Rivalry worker started")
    while not stopping:
        job = worker.run_once()
        if job is None:
            time.sleep(interval)
    logger.info("Rivalry worker stopped")


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("RIVALRY_LOG_LEVEL", "INFO"))
    run_worker()

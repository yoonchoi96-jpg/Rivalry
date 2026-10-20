import signal

from core.jobs.models import JobType
import core.jobs.entrypoint as entrypoint


def test_run_worker_stops_on_signal(monkeypatch):
    handlers = {}

    def fake_signal(signum, handler):
        handlers[signum] = handler

    class FakeWorker:
        def __init__(self, queue, handlers=None):
            self.queue = queue
            self.handlers = handlers

        def run_once(self):
            assert self.handlers
            assert JobType.COLLECT_COMPETITOR in self.handlers
            handlers[signal.SIGTERM](signal.SIGTERM, None)
            return None

    monkeypatch.setattr(entrypoint, "JobWorker", FakeWorker)
    monkeypatch.setattr(entrypoint, "JobHandlers", lambda store, **_kwargs: type(
        "Handlers",
        (),
        {"registry": lambda self: {JobType.COLLECT_COMPETITOR: object()}},
    )())
    monkeypatch.setattr(entrypoint, "intelligence_store", object())
    monkeypatch.setattr(entrypoint, "job_queue", object())
    monkeypatch.setattr(entrypoint.signal, "signal", fake_signal)
    monkeypatch.setattr(entrypoint.time, "sleep", lambda _interval: None)

    entrypoint.run_worker(poll_interval=0)

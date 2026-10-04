import signal

import core.jobs.entrypoint as entrypoint


def test_run_worker_stops_on_signal(monkeypatch):
    handlers = {}

    def fake_signal(signum, handler):
        handlers[signum] = handler

    class FakeWorker:
        def __init__(self, queue):
            self.queue = queue

        def run_once(self):
            handlers[signal.SIGTERM](signal.SIGTERM, None)
            return None

    monkeypatch.setattr(entrypoint, "JobWorker", FakeWorker)
    monkeypatch.setattr(entrypoint, "job_queue", object())
    monkeypatch.setattr(entrypoint.signal, "signal", fake_signal)
    monkeypatch.setattr(entrypoint.time, "sleep", lambda _interval: None)

    entrypoint.run_worker(poll_interval=0)

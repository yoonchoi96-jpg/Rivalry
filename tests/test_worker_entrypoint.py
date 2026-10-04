import core.jobs.entrypoint as entrypoint


def test_run_worker_stops_on_signal(monkeypatch):
    class FakeWorker:
        def __init__(self, queue):
            self.queue = queue

        def run_once(self):
            entrypoint.stop_requested = True
            return None

    monkeypatch.setattr(entrypoint, "JobWorker", FakeWorker)
    monkeypatch.setattr(entrypoint, "job_queue", object())
    monkeypatch.setattr(entrypoint.time, "sleep", lambda _interval: None)

    entrypoint.stop_requested = False
    entrypoint.run_worker(poll_interval=0)
    assert entrypoint.stop_requested is True

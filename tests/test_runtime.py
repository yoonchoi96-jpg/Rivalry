import importlib

import pytest


def _reload_runtime(monkeypatch, *, production: bool, database: str = "", redis: str = ""):
    monkeypatch.setenv("RIVALRY_ENV", "production" if production else "test")
    monkeypatch.setenv("RIVALRY_DATABASE_URL", database)
    monkeypatch.setenv("RIVALRY_REDIS_URL", redis)
    import core.jobs.runtime as runtime

    return importlib.reload(runtime)


def test_production_requires_both_database_and_redis(monkeypatch):
    with pytest.raises(RuntimeError, match="requires both"):
        _reload_runtime(monkeypatch, production=True)


def test_production_requires_both_database_and_redis_when_database_only(monkeypatch):
    with pytest.raises(RuntimeError, match="requires both"):
        _reload_runtime(monkeypatch, production=True, database="postgresql://db")


def test_production_requires_redis_when_database_is_configured(monkeypatch):
    with pytest.raises(RuntimeError, match="requires both"):
        _reload_runtime(monkeypatch, production=True, redis="redis://redis")


def test_non_production_keeps_local_fallbacks(monkeypatch):
    runtime = _reload_runtime(monkeypatch, production=False)
    assert runtime.job_store.__class__.__name__ == "InMemoryJobStore"
    assert runtime.job_queue.__class__.__name__ == "InMemoryJobQueue"

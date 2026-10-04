import pytest

_ENV_PREFIXES = ("RIVALRY_", "OPENAI_", "ANTHROPIC_", "GEMINI_", "PERPLEXITY_", "NAVER_", "DASHSCOPE_")
_KEEP = {"RIVALRY_TEST_DATABASE_URL"}


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch):
    """Keep tests hermetic: drop provider keys and service URLs from the host env."""
    import os

    for key in list(os.environ):
        if key.startswith(_ENV_PREFIXES) and key not in _KEEP:
            monkeypatch.delenv(key, raising=False)

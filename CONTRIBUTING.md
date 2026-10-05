# Contributing

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
cp .env.example .env   # never commit .env or real keys
```

## Checks
```bash
pytest -q                               # unit tests (integration tests skip without RIVALRY_TEST_DATABASE_URL)
pip install ruff && ruff check . --select E9,F63,F7,F82
```

## Guidelines
- Inspect before changing; keep changes small and incremental.
- Migrations are forward-only and non-destructive (`db/migrations/`).
- Source-specific logic goes in `adapters/`; the core works on normalized data.
- Keep provenance on observations; AI output must reference evidence and never overwrite raw data.
- Jobs must be idempotent. Never commit secrets.

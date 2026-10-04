from __future__ import annotations

import os
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schema.sql"
MIGRATIONS = ROOT / "migrations"


def migrate(dsn: str) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(SCHEMA.read_text(encoding="utf-8"))
        for path in sorted(MIGRATIONS.glob("*.sql")):
            cur.execute(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    dsn = os.getenv("RIVALRY_DATABASE_URL", "").strip()
    if not dsn:
        raise SystemExit("RIVALRY_DATABASE_URL is required")
    migrate(dsn)

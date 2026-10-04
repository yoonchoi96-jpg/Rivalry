from __future__ import annotations

import json
from typing import Any, Callable

import psycopg
from psycopg.types.json import Jsonb

from .models import Job
from .store import JobStore


class PostgresJobStore(JobStore):
    """Durable job state store shared by API and worker processes."""

    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn = dsn
        self._connect = connect

    def save(self, job: Job) -> Job:
        row = job.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (
                    id, type, payload_json, status, created_at, started_at,
                    finished_at, error, result_json, attempts, max_attempts
                )
                VALUES (
                    %(id)s, %(type)s, %(payload_json)s, %(status)s,
                    %(created_at)s::timestamptz, %(started_at)s::timestamptz,
                    %(finished_at)s::timestamptz, %(error)s, %(result_json)s,
                    %(attempts)s, %(max_attempts)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    status=EXCLUDED.status, started_at=EXCLUDED.started_at,
                    finished_at=EXCLUDED.finished_at, error=EXCLUDED.error,
                    result_json=EXCLUDED.result_json, attempts=EXCLUDED.attempts,
                    max_attempts=EXCLUDED.max_attempts
                """,
                {
                    **row,
                    "type": job.type.value,
                    "payload_json": Jsonb(row["payload"]),
                    "result_json": Jsonb(row["result"]) if row["result"] is not None else None,
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                },
            )
        return job

    def get(self, job_id: str) -> Job | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, type, payload_json, status, created_at, started_at,
                       finished_at, error, result_json, attempts, max_attempts
                FROM jobs WHERE id=%s
                """,
                (job_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return Job(
            id=row[0], type=row[1], payload=row[2], status=row[3],
            created_at=row[4].isoformat() if hasattr(row[4], "isoformat") else row[4],
            started_at=row[5].isoformat() if row[5] and hasattr(row[5], "isoformat") else row[5],
            finished_at=row[6].isoformat() if row[6] and hasattr(row[6], "isoformat") else row[6],
            error=row[7], result=row[8], attempts=row[9], max_attempts=row[10],
        )

from __future__ import annotations

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
                    id, type, payload_json, idempotency_key, status, created_at, started_at,
                    finished_at, error, result_json, attempts, max_attempts, next_attempt_at
                )
                VALUES (
                    %(id)s, %(type)s, %(payload_json)s, %(idempotency_key)s, %(status)s,
                    %(created_at)s::timestamptz, %(started_at)s::timestamptz,
                    %(finished_at)s::timestamptz, %(error)s, %(result_json)s,
                    %(attempts)s, %(max_attempts)s, %(next_attempt_at)s::timestamptz
                )
                ON CONFLICT DO NOTHING
                """,
                {
                    **row,
                    "type": job.type.value,
                    "payload_json": Jsonb(row["payload"]),
                    "result_json": Jsonb(row["result"]) if row["result"] is not None else None,
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                    "next_attempt_at": row["next_attempt_at"],
                },
            )
            cur.execute(
                """
                UPDATE jobs SET
                    type=%(type)s,
                    payload_json=%(payload_json)s,
                    idempotency_key=%(idempotency_key)s,
                    status=%(status)s,
                    started_at=%(started_at)s::timestamptz,
                    finished_at=%(finished_at)s::timestamptz,
                    error=%(error)s,
                    result_json=%(result_json)s,
                    attempts=%(attempts)s,
                    max_attempts=%(max_attempts)s,
                    next_attempt_at=%(next_attempt_at)s::timestamptz
                WHERE id=%(id)s
                """,
                {
                    **row,
                    "type": job.type.value,
                    "payload_json": Jsonb(row["payload"]),
                    "result_json": Jsonb(row["result"]) if row["result"] is not None else None,
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                    "next_attempt_at": row["next_attempt_at"],
                },
            )
            cur.execute(
                """
                SELECT id, type, payload_json, idempotency_key, status, created_at, started_at,
                       finished_at, error, result_json, attempts, max_attempts, next_attempt_at
                FROM jobs WHERE id=%s
                """,
                (job.id,),
            )
            row_by_id = cur.fetchone()
            if row_by_id is None and job.idempotency_key:
                cur.execute(
                    """
                    SELECT id, type, payload_json, idempotency_key, status, created_at, started_at,
                           finished_at, error, result_json, attempts, max_attempts, next_attempt_at
                    FROM jobs WHERE idempotency_key=%s
                    """,
                    (job.idempotency_key,),
                )
                row_by_id = cur.fetchone()
        if row_by_id is None:
            return job
        return self._row_to_job(row_by_id)

    @staticmethod
    def _row_to_job(row: tuple[Any, ...]) -> Job:
        return Job(
            id=row[0],
            type=row[1],
            payload=row[2],
            idempotency_key=row[3],
            status=row[4],
            created_at=row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
            started_at=row[6].isoformat() if row[6] and hasattr(row[6], "isoformat") else row[6],
            finished_at=row[7].isoformat() if row[7] and hasattr(row[7], "isoformat") else row[7],
            error=row[8],
            result=row[9],
            attempts=row[10],
            max_attempts=row[11],
            next_attempt_at=row[12].isoformat() if row[12] and hasattr(row[12], "isoformat") else row[12],
        )

    def get(self, job_id: str) -> Job | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, type, payload_json, idempotency_key, status, created_at, started_at,
                       finished_at, error, result_json, attempts, max_attempts, next_attempt_at
                FROM jobs WHERE id=%s
                """,
                (job_id,),
            )
            row = cur.fetchone()
        return self._row_to_job(row) if row else None

    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, type, payload_json, idempotency_key, status, created_at, started_at,
                       finished_at, error, result_json, attempts, max_attempts, next_attempt_at
                FROM jobs WHERE idempotency_key=%s
                """,
                (idempotency_key,),
            )
            row = cur.fetchone()
        return self._row_to_job(row) if row else None

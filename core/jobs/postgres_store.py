from __future__ import annotations

from typing import Any, Callable

import psycopg
from psycopg.types.json import Jsonb

from .models import Job
from .store import JobStore


class PostgresJobStore(JobStore):
    """Durable job state store shared by API and worker processes."""

    _SELECT = """
        SELECT id, type, payload_json, idempotency_key, status, created_at, started_at,
               finished_at, error, result_json, attempts, max_attempts, next_attempt_at,
               enqueue_version
        FROM jobs
    """

    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn = dsn
        self._connect = connect

    @staticmethod
    def _params(job: Job) -> dict[str, object]:
        row = job.model_dump(mode="json")
        return {
            **row,
            "type": job.type.value,
            "payload_json": Jsonb(row["payload"]),
            "result_json": Jsonb(row["result"]) if row["result"] is not None else None,
        }

    def save(self, job: Job) -> Job:
        params = self._params(job)
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (
                    id, type, payload_json, idempotency_key, status, created_at, started_at,
                    finished_at, error, result_json, attempts, max_attempts, next_attempt_at,
                    enqueue_version
                )
                VALUES (
                    %(id)s, %(type)s, %(payload_json)s, %(idempotency_key)s, %(status)s,
                    %(created_at)s::timestamptz, %(started_at)s::timestamptz,
                    %(finished_at)s::timestamptz, %(error)s, %(result_json)s,
                    %(attempts)s, %(max_attempts)s, %(next_attempt_at)s::timestamptz,
                    %(enqueue_version)s
                )
                ON CONFLICT DO NOTHING
                """,
                params,
            )
            cur.execute(
                """
                UPDATE jobs SET
                    type=%(type)s, payload_json=%(payload_json)s,
                    idempotency_key=%(idempotency_key)s, status=%(status)s,
                    started_at=%(started_at)s::timestamptz,
                    finished_at=%(finished_at)s::timestamptz, error=%(error)s,
                    result_json=%(result_json)s, attempts=%(attempts)s,
                    max_attempts=%(max_attempts)s,
                    next_attempt_at=%(next_attempt_at)s::timestamptz,
                    enqueue_version=%(enqueue_version)s
                WHERE id=%(id)s
                """,
                params,
            )
            cur.execute(self._SELECT + " WHERE id=%s", (job.id,))
            row = cur.fetchone()
            if row is None and job.idempotency_key:
                cur.execute(self._SELECT + " WHERE idempotency_key=%s", (job.idempotency_key,))
                row = cur.fetchone()
        return self._row_to_job(row) if row else job

    def prepare_enqueue(self, job: Job) -> Job:
        params = self._params(job)
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            inserted = False
            if job.idempotency_key:
                # The partial unique index is the concurrency authority. The
                # pre-check is only a fast path; concurrent callers can race.
                cur.execute(
                    """
                    INSERT INTO jobs (
                        id, type, payload_json, idempotency_key, status, created_at, started_at,
                        finished_at, error, result_json, attempts, max_attempts, next_attempt_at,
                        enqueue_version
                    )
                    VALUES (
                        %(id)s, %(type)s, %(payload_json)s, %(idempotency_key)s, %(status)s,
                        %(created_at)s::timestamptz, %(started_at)s::timestamptz,
                        %(finished_at)s::timestamptz, %(error)s, %(result_json)s,
                        %(attempts)s, %(max_attempts)s, %(next_attempt_at)s::timestamptz,
                        %(enqueue_version)s
                    )
                    ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING
                    RETURNING id
                    """,
                    params,
                )
                inserted = cur.fetchone() is not None
                if not inserted:
                    cur.execute(self._SELECT + " WHERE idempotency_key=%s", (job.idempotency_key,))
                    existing = cur.fetchone()
                    if existing is None:
                        raise RuntimeError("job idempotency conflict could not be resolved")
                    return self._row_to_job(existing)

            if not job.idempotency_key:
                cur.execute(
                    """
                    INSERT INTO jobs (
                        id, type, payload_json, idempotency_key, status, created_at, started_at,
                        finished_at, error, result_json, attempts, max_attempts, next_attempt_at,
                        enqueue_version
                    )
                    VALUES (
                        %(id)s, %(type)s, %(payload_json)s, %(idempotency_key)s, %(status)s,
                        %(created_at)s::timestamptz, %(started_at)s::timestamptz,
                        %(finished_at)s::timestamptz, %(error)s, %(result_json)s,
                        %(attempts)s, %(max_attempts)s, %(next_attempt_at)s::timestamptz,
                        %(enqueue_version)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        status=EXCLUDED.status,
                        payload_json=EXCLUDED.payload_json,
                        enqueue_version=EXCLUDED.enqueue_version,
                        next_attempt_at=EXCLUDED.next_attempt_at
                    """,
                    params,
                )

            cur.execute(
                """
                INSERT INTO job_outbox (job_id, enqueue_version, created_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    enqueue_version=EXCLUDED.enqueue_version,
                    created_at=EXCLUDED.created_at,
                    published_at=NULL,
                    last_error=NULL
                """,
                (job.id, job.enqueue_version),
            )
            cur.execute(self._SELECT + " WHERE id=%s", (job.id,))
            row = cur.fetchone()
        return self._row_to_job(row) if row else job

    def pending_outbox(self, limit: int = 100) -> list[Job]:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                self._SELECT.replace("FROM jobs", "FROM job_outbox o JOIN jobs j ON j.id=o.job_id") +
                " WHERE o.published_at IS NULL "
                "AND (j.next_attempt_at IS NULL OR j.next_attempt_at <= NOW()) "
                "ORDER BY o.created_at ASC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        return [self._row_to_job(row) for row in rows]

    @staticmethod
    def _row_to_job(row: tuple[Any, ...]) -> Job:
        return Job(
            id=row[0], type=row[1], payload=row[2], idempotency_key=row[3], status=row[4],
            created_at=row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
            started_at=row[6].isoformat() if row[6] and hasattr(row[6], "isoformat") else row[6],
            finished_at=row[7].isoformat() if row[7] and hasattr(row[7], "isoformat") else row[7],
            error=row[8], result=row[9], attempts=row[10], max_attempts=row[11],
            next_attempt_at=row[12].isoformat() if row[12] and hasattr(row[12], "isoformat") else row[12],
            enqueue_version=row[13],
        )

    def get(self, job_id: str) -> Job | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(self._SELECT + " WHERE id=%s", (job_id,))
            row = cur.fetchone()
        return self._row_to_job(row) if row else None

    def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(self._SELECT + " WHERE idempotency_key=%s", (idempotency_key,))
            row = cur.fetchone()
        return self._row_to_job(row) if row else None

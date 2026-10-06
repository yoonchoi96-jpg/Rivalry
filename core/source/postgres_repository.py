from __future__ import annotations

from typing import Any, Callable

import psycopg
from psycopg.types.json import Jsonb

from .models import SourceKind, SourceProfile
from .repository import SourceRepository


class PostgresSourceRepository(SourceRepository):
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save(self, source: SourceProfile) -> SourceProfile:
        row = source.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO source_profiles
                (id,name,kind,reliability,coverage,cost,latency,freshness_minutes,
                 rate_limit_per_minute,normalization_quality,capabilities_json)
                VALUES (%(id)s,%(name)s,%(kind)s,%(reliability)s,%(coverage)s,%(cost)s,%(latency)s,
                        %(freshness_minutes)s,%(rate_limit_per_minute)s,%(normalization_quality)s,%(capabilities)s)
                ON CONFLICT (id) DO UPDATE SET
                    name=EXCLUDED.name,kind=EXCLUDED.kind,reliability=EXCLUDED.reliability,
                    coverage=EXCLUDED.coverage,cost=EXCLUDED.cost,latency=EXCLUDED.latency,
                    freshness_minutes=EXCLUDED.freshness_minutes,
                    rate_limit_per_minute=EXCLUDED.rate_limit_per_minute,
                    normalization_quality=EXCLUDED.normalization_quality,
                    capabilities_json=EXCLUDED.capabilities_json
            """, {**row, "kind": source.kind.value, "capabilities": Jsonb(row["capabilities"])})
        return source

    def get(self, source_id: str) -> SourceProfile | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id,name,kind,reliability,coverage,cost,latency,freshness_minutes,
                       rate_limit_per_minute,normalization_quality,capabilities_json
                FROM source_profiles WHERE id=%s
            """, (source_id,))
            row = cur.fetchone()
        return self._row(row) if row else None

    def list(self) -> list[SourceProfile]:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id,name,kind,reliability,coverage,cost,latency,freshness_minutes,
                       rate_limit_per_minute,normalization_quality,capabilities_json
                FROM source_profiles ORDER BY reliability DESC, name
            """)
            rows = cur.fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: tuple[Any, ...]) -> SourceProfile:
        return SourceProfile(
            id=row[0], name=row[1], kind=SourceKind(row[2]), reliability=row[3],
            coverage=row[4], cost=row[5], latency=row[6], freshness_minutes=row[7],
            rate_limit_per_minute=row[8], normalization_quality=row[9],
            capabilities=list(row[10] or []),
        )

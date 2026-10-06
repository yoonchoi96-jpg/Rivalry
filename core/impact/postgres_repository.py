from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import BusinessImpact


class PostgresImpactRepository:
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save(self, impact: BusinessImpact) -> BusinessImpact:
        row = impact.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO business_impacts
                (id,business_id,entity_id,signal_id,factor_key,exposure,magnitude,
                 magnitude_low,magnitude_high,confidence,significance,rationale,
                 evidence_ids_json,observation_ids_json,measurement_ids_json)
                VALUES (%(id)s,%(business_id)s,%(entity_id)s,%(signal_id)s,%(factor_key)s,
                        %(exposure)s,%(magnitude)s,%(magnitude_low)s,%(magnitude_high)s,
                        %(confidence)s,%(significance)s,%(rationale)s,%(evidence_ids)s,
                        %(observation_ids)s,%(measurement_ids)s)
                ON CONFLICT (id) DO UPDATE SET exposure=EXCLUDED.exposure,
                magnitude=EXCLUDED.magnitude,magnitude_low=EXCLUDED.magnitude_low,
                magnitude_high=EXCLUDED.magnitude_high,confidence=EXCLUDED.confidence,
                significance=EXCLUDED.significance,rationale=EXCLUDED.rationale,
                evidence_ids_json=EXCLUDED.evidence_ids_json,
                observation_ids_json=EXCLUDED.observation_ids_json,
                measurement_ids_json=EXCLUDED.measurement_ids_json""",
                {**row, "evidence_ids": Jsonb(row["evidence_ids"]),
                 "observation_ids": Jsonb(row["observation_ids"]),
                 "measurement_ids": Jsonb(row["measurement_ids"])},
            )
        return impact

    def get(self, impact_id: str) -> BusinessImpact | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT id,business_id,entity_id,signal_id,factor_key,exposure,magnitude,
                magnitude_low,magnitude_high,confidence,significance,rationale,
                evidence_ids_json,observation_ids_json,measurement_ids_json
                FROM business_impacts WHERE id=%s""",
                (impact_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return BusinessImpact(
            id=row[0],business_id=row[1],entity_id=row[2],signal_id=row[3],factor_key=row[4],
            exposure=row[5],magnitude=row[6],magnitude_low=row[7],magnitude_high=row[8],
            confidence=row[9],significance=row[10],rationale=row[11] or "",
            evidence_ids=list(row[12] or []),observation_ids=list(row[13] or []),
            measurement_ids=list(row[14] or []),
        )

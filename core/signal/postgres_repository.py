from __future__ import annotations

from collections.abc import Callable
from typing import Any
import psycopg
from psycopg.types.json import Jsonb

from .models import Signal, SignalDirection, SignalKind
from .repository import SignalRepository


class PostgresSignalRepository(SignalRepository):
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save(self, signal: Signal) -> Signal:
        row = signal.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO signals
                (id,entity_id,definition_key,signal_kind,direction,current_value,reference_value,
                 delta,delta_pct,detected_at,observation_ids_json,measurement_ids_json,
                 confidence,significance,rationale,freshness_minutes)
                VALUES (%(id)s,%(entity_id)s,%(definition_key)s,%(signal_kind)s,%(direction)s,
                        %(current_value)s,%(reference_value)s,%(delta)s,%(delta_pct)s,%(detected_at)s,
                        %(observation_ids)s,%(measurement_ids)s,%(confidence)s,%(significance)s,
                        %(rationale)s,%(freshness_minutes)s)
                ON CONFLICT (id) DO UPDATE SET current_value=EXCLUDED.current_value,
                reference_value=EXCLUDED.reference_value,delta=EXCLUDED.delta,delta_pct=EXCLUDED.delta_pct,
                detected_at=EXCLUDED.detected_at,observation_ids_json=EXCLUDED.observation_ids_json,
                measurement_ids_json=EXCLUDED.measurement_ids_json,confidence=EXCLUDED.confidence,
                significance=EXCLUDED.significance,rationale=EXCLUDED.rationale,
                freshness_minutes=EXCLUDED.freshness_minutes""",
                {**row, "observation_ids": Jsonb(row["observation_ids"]),
                 "measurement_ids": Jsonb(row["measurement_ids"])},
            )
        return signal

    def get(self, signal_id: str) -> Signal | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT id,entity_id,definition_key,signal_kind,direction,current_value,
                reference_value,delta,delta_pct,detected_at,observation_ids_json,
                measurement_ids_json,confidence,significance,rationale,freshness_minutes
                FROM signals WHERE id=%s""",
                (signal_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return Signal(
            id=row[0], entity_id=row[1], definition_key=row[2],
            signal_kind=SignalKind(row[3]), direction=SignalDirection(row[4]),
            current_value=row[5], reference_value=row[6], delta=row[7],
            delta_pct=row[8], detected_at=row[9].isoformat() if hasattr(row[9], "isoformat") else row[9],
            observation_ids=list(row[10] or []), measurement_ids=list(row[11] or []),
            confidence=row[12], significance=row[13], rationale=row[14] or "",
            freshness_minutes=row[15],
        )

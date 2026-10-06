from __future__ import annotations
from collections.abc import Callable
from typing import Any
import psycopg
from psycopg.types.json import Jsonb
from .models import Measurement, MeasurementQuality
from .repository import MeasurementRepository

class PostgresMeasurementRepository(MeasurementRepository):
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn: raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect
    def save(self, measurement: Measurement) -> Measurement:
        row=measurement.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO measurements
                (id,definition_key,entity_id,value,unit,measured_at,time_window,geography,confidence,quality,formula,model_version,observation_ids_json)
                VALUES (%(id)s,%(definition_key)s,%(entity_id)s,%(value)s,%(unit)s,%(measured_at)s,%(time_window)s,%(geography)s,%(confidence)s,%(quality)s,%(formula)s,%(model_version)s,%(observation_ids)s)
                ON CONFLICT (id) DO UPDATE SET value=EXCLUDED.value,unit=EXCLUDED.unit,measured_at=EXCLUDED.measured_at,
                time_window=EXCLUDED.time_window,geography=EXCLUDED.geography,confidence=EXCLUDED.confidence,
                quality=EXCLUDED.quality,formula=EXCLUDED.formula,model_version=EXCLUDED.model_version,observation_ids_json=EXCLUDED.observation_ids_json""",
                {**row,"observation_ids":Jsonb(row["observation_ids"])})
        return measurement
    def get(self, measurement_id: str) -> Measurement | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""SELECT id,definition_key,entity_id,value,unit,measured_at,time_window,geography,confidence,quality,formula,model_version,observation_ids_json
                FROM measurements WHERE id=%s""",(measurement_id,))
            row=cur.fetchone()
        if row is None: return None
        return Measurement(id=row[0],definition_key=row[1],entity_id=row[2],value=row[3],unit=row[4],measured_at=row[5].isoformat() if hasattr(row[5],"isoformat") else row[5],time_window=row[6],geography=row[7],confidence=row[8],quality=MeasurementQuality(row[9]),formula=row[10],model_version=row[11],observation_ids=list(row[12] or []))

from __future__ import annotations

from collections.abc import Callable
from typing import Any
import psycopg
from psycopg.types.json import Jsonb
from .models import Observation
from .repository import ObservationRepository
from core.evidence.models import AccessMethod, KnowledgeKind


class PostgresObservationRepository(ObservationRepository):
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn: raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save(self, observation: Observation) -> Observation:
        row=observation.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO observations
                (id,entity_id,entity_type,metric,raw_value,normalized_value,unit,currency,geography,observed_at,source_id,evidence_id,access_method,confidence,knowledge_kind,provenance_json,model_version)
                VALUES (%(id)s,%(entity_id)s,%(entity_type)s,%(metric)s,%(raw_value)s,%(normalized_value)s,%(unit)s,%(currency)s,%(geography)s,%(observed_at)s,%(source_id)s,%(evidence_id)s,%(access_method)s,%(confidence)s,%(knowledge_kind)s,%(provenance)s,%(model_version)s)
                ON CONFLICT (id) DO UPDATE SET raw_value=EXCLUDED.raw_value,normalized_value=EXCLUDED.normalized_value,unit=EXCLUDED.unit,currency=EXCLUDED.currency,
                geography=EXCLUDED.geography,observed_at=EXCLUDED.observed_at,evidence_id=EXCLUDED.evidence_id,confidence=EXCLUDED.confidence,
                knowledge_kind=EXCLUDED.knowledge_kind,provenance_json=EXCLUDED.provenance_json,model_version=EXCLUDED.model_version""",
                {**row,"raw_value":Jsonb(row["raw_value"]),"provenance":Jsonb(row["provenance"])})
        return observation

    def get(self, observation_id: str) -> Observation | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""SELECT id,entity_id,entity_type,metric,raw_value,normalized_value,unit,currency,geography,observed_at,source_id,evidence_id,access_method,confidence,knowledge_kind,provenance_json,model_version
                FROM observations WHERE id=%s""",(observation_id,))
            row=cur.fetchone()
        if row is None: return None
        return Observation(id=row[0],entity_id=row[1],entity_type=row[2],metric=row[3],raw_value=row[4],normalized_value=row[5],unit=row[6],currency=row[7],geography=row[8],observed_at=row[9],source_id=row[10],evidence_id=row[11],access_method=AccessMethod(row[12]),confidence=row[13],knowledge_kind=KnowledgeKind(row[14]),provenance=row[15] or {},model_version=row[16])

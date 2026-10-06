from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import AccessMethod, Evidence, EvidenceSource, KnowledgeKind
from .repository import EvidenceRepository


class PostgresEvidenceRepository(EvidenceRepository):
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save_source(self, source: EvidenceSource) -> EvidenceSource:
        row = source.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO evidence_sources
                (id,name,url,source_type,access_method,retrieved_at,reliability,coverage,content_hash,metadata_json)
                VALUES (%(id)s,%(name)s,%(url)s,%(source_type)s,%(access_method)s,%(retrieved_at)s,%(reliability)s,%(coverage)s,%(content_hash)s,%(metadata)s)
                ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name,url=EXCLUDED.url,source_type=EXCLUDED.source_type,
                access_method=EXCLUDED.access_method,retrieved_at=EXCLUDED.retrieved_at,reliability=EXCLUDED.reliability,
                coverage=EXCLUDED.coverage,content_hash=EXCLUDED.content_hash,metadata_json=EXCLUDED.metadata_json""",
                {**row, "metadata": Jsonb(row["metadata"])})
        return source

    def save(self, evidence: Evidence) -> Evidence:
        row = evidence.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO evidence
                (id,source_id,statement,captured_at,locator,excerpt,confidence,knowledge_kind)
                VALUES (%(id)s,%(source_id)s,%(statement)s,%(captured_at)s,%(locator)s,%(excerpt)s,%(confidence)s,%(knowledge_kind)s)
                ON CONFLICT (id) DO UPDATE SET statement=EXCLUDED.statement,captured_at=EXCLUDED.captured_at,
                locator=EXCLUDED.locator,excerpt=EXCLUDED.excerpt,confidence=EXCLUDED.confidence,knowledge_kind=EXCLUDED.knowledge_kind""", row)
        return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT id,source_id,statement,captured_at,locator,excerpt,confidence,knowledge_kind FROM evidence WHERE id=%s",(evidence_id,))
            row=cur.fetchone()
        if row is None: return None
        return Evidence(id=row[0],source_id=row[1],statement=row[2],captured_at=row[3],locator=row[4],excerpt=row[5],confidence=row[6],knowledge_kind=KnowledgeKind(row[7]))

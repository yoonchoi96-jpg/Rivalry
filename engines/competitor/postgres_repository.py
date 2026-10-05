from __future__ import annotations

from typing import Any, Callable

import psycopg

from .models import Competitor


class PostgresCompetitorRepository:
    """PostgreSQL-backed competitor repository shared by API and worker processes."""

    def __init__(
        self,
        dsn: str,
        *,
        connect: Callable[..., Any] = psycopg.connect,
    ) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn = dsn
        self._connect = connect

    def list(self) -> list[Competitor]:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, business_id, name, platform, strategic,
                       similarity_score, market_relevance
                FROM competitors
                ORDER BY id
                """
            )
            rows = cur.fetchall()
        return [self._from_row(row) for row in rows]

    def add(self, competitor: Competitor) -> Competitor:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO competitors (
                    id, business_id, name, platform, strategic,
                    similarity_score, market_relevance
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    business_id = EXCLUDED.business_id,
                    name = EXCLUDED.name,
                    platform = EXCLUDED.platform,
                    strategic = EXCLUDED.strategic,
                    similarity_score = EXCLUDED.similarity_score,
                    market_relevance = EXCLUDED.market_relevance
                """,
                (
                    competitor.id,
                    competitor.business_id,
                    competitor.name,
                    competitor.platform,
                    competitor.strategic,
                    competitor.similarity_score,
                    competitor.market_relevance,
                ),
            )
        return competitor

    @staticmethod
    def _from_row(row: tuple[Any, ...]) -> Competitor:
        return Competitor(
            id=row[0],
            business_id=row[1],
            name=row[2],
            platform=row[3],
            strategic=row[4],
            similarity_score=row[5],
            market_relevance=row[6],
        )

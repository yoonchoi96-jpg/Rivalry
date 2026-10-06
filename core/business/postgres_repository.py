from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .entity import BusinessEntity
from .repository import BusinessRepository


class PostgresBusinessRepository(BusinessRepository):
    """PostgreSQL-backed canonical Business Entity repository."""

    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn = dsn
        self._connect = connect

    def save(self, business: BusinessEntity) -> BusinessEntity:
        row = business.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO businesses (
                    id, name, country_code, business_type, channel,
                    location, website_url, goal, profile_json
                ) VALUES (
                    %(id)s, %(name)s, %(country_code)s, %(business_type)s,
                    %(channel)s, %(location)s, %(website_url)s, %(goal)s,
                    %(profile_json)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    country_code = EXCLUDED.country_code,
                    business_type = EXCLUDED.business_type,
                    channel = EXCLUDED.channel,
                    location = EXCLUDED.location,
                    website_url = EXCLUDED.website_url,
                    goal = EXCLUDED.goal,
                    profile_json = EXCLUDED.profile_json
                """,
                {**row, "profile_json": Jsonb(row["profile"])},
            )
        return BusinessEntity.model_validate(row)

    def get(self, business_id: str) -> BusinessEntity | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, country_code, business_type, channel,
                       location, website_url, goal, profile_json
                FROM businesses
                WHERE id = %s
                """,
                (business_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return BusinessEntity(
            id=row[0], name=row[1], country_code=row[2], business_type=row[3],
            channel=row[4], location=row[5], website_url=row[6], goal=row[7],
            profile=dict(row[8] or {}),
        )

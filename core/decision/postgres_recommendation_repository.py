from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import DecisionRecommendation


class PostgresDecisionRecommendationRepository:
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save(self, recommendation: DecisionRecommendation) -> DecisionRecommendation:
        row = recommendation.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO decision_recommendations
                (impact_id,business_id,signal_id,action,priority,rationale,confidence,factor_key,policy_id,recommendation_json)
                VALUES (%(impact_id)s,%(business_id)s,%(signal_id)s,%(action)s,%(priority)s,%(rationale)s,
                        %(confidence)s,%(factor_key)s,%(policy_id)s,%(recommendation_json)s)
                ON CONFLICT (impact_id) DO UPDATE SET action=EXCLUDED.action,priority=EXCLUDED.priority,
                rationale=EXCLUDED.rationale,confidence=EXCLUDED.confidence,factor_key=EXCLUDED.factor_key,
                policy_id=EXCLUDED.policy_id,recommendation_json=EXCLUDED.recommendation_json,updated_at=NOW()""",
                {**row, "recommendation_json": Jsonb(row)},
            )
        return DecisionRecommendation.model_validate(row)

    def get(self, recommendation_id: str) -> DecisionRecommendation | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT recommendation_json FROM decision_recommendations WHERE impact_id=%s",
                (recommendation_id,),
            )
            row = cur.fetchone()
        return None if row is None else DecisionRecommendation.model_validate(row[0])

    def list_for_business(self, business_id: str) -> list[DecisionRecommendation]:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT recommendation_json FROM decision_recommendations WHERE business_id=%s ORDER BY updated_at DESC",
                (business_id,),
            )
            rows = cur.fetchall()
        return [DecisionRecommendation.model_validate(row[0]) for row in rows]

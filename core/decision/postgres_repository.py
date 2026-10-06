from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import DecisionPolicy


class PostgresDecisionPolicyRepository:
    def __init__(self, dsn: str, *, connect: Callable[..., Any] = psycopg.connect) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN must not be empty")
        self.dsn, self._connect = dsn, connect

    def save(self, policy_id: str, policy: DecisionPolicy) -> DecisionPolicy:
        stored = DecisionPolicy.model_validate(policy.model_dump(mode="json"))
        stored.id = policy_id
        row = stored.model_dump(mode="json")
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO decision_policies (id,name,policy_json) VALUES (%(id)s,%(name)s,%(policy_json)s) "
                "ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, policy_json=EXCLUDED.policy_json, updated_at=NOW()",
                {"id": policy_id, "name": stored.name, "policy_json": Jsonb(row)},
            )
        return DecisionPolicy.model_validate(row)

    def get(self, policy_id: str) -> DecisionPolicy | None:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT policy_json FROM decision_policies WHERE id=%s", (policy_id,))
            row = cur.fetchone()
        return None if row is None else DecisionPolicy.model_validate(row[0])

    def list(self) -> list[DecisionPolicy]:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT policy_json FROM decision_policies ORDER BY id")
            rows = cur.fetchall()
        return [DecisionPolicy.model_validate(row[0]) for row in rows]

    def remove(self, policy_id: str) -> bool:
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM decision_policies WHERE id=%s", (policy_id,))
            return cur.rowcount > 0

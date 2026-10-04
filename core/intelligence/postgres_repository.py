from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import Change, CostSignal, Prediction, Review
from .repository import IntelligenceRepository


class PostgresIntelligenceRepository(IntelligenceRepository):
    """PostgreSQL-backed repository shared safely by API/worker processes."""

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

    def _connection(self):
        return self._connect(self.dsn)

    def record_changes(self, changes: list[Change]) -> None:
        if not changes:
            return
        with self._connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO changes (
                    id, business_id, competitor_id, type, before_json, after_json,
                    detected_at, magnitude, severity, impact_score, confidence,
                    evidence_json, source
                )
                VALUES (
                    %(id)s, %(business_id)s, %(competitor_id)s, %(type)s,
                    %(before_json)s, %(after_json)s, %(detected_at)s::timestamptz,
                    %(magnitude)s, %(severity)s, %(impact_score)s, %(confidence)s,
                    %(evidence_json)s, %(source)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    business_id = EXCLUDED.business_id,
                    competitor_id = EXCLUDED.competitor_id,
                    type = EXCLUDED.type,
                    before_json = EXCLUDED.before_json,
                    after_json = EXCLUDED.after_json,
                    detected_at = EXCLUDED.detected_at,
                    magnitude = EXCLUDED.magnitude,
                    severity = EXCLUDED.severity,
                    impact_score = EXCLUDED.impact_score,
                    confidence = EXCLUDED.confidence,
                    evidence_json = EXCLUDED.evidence_json,
                    source = EXCLUDED.source
                """,
                [self._change_row(change) for change in changes],
            )

    def record_reviews(self, reviews: list[Review]) -> None:
        if not reviews:
            return
        with self._connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO reviews (
                    id, competitor_id, rating, text, created_at,
                    sentiment, topics_json, product_id, source, confidence
                )
                VALUES (
                    %(id)s, %(competitor_id)s, %(rating)s, %(text)s,
                    %(created_at)s::timestamptz, %(sentiment)s, %(topics_json)s,
                    %(product_id)s, %(source)s, %(confidence)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    competitor_id = EXCLUDED.competitor_id,
                    rating = EXCLUDED.rating,
                    text = EXCLUDED.text,
                    created_at = EXCLUDED.created_at,
                    sentiment = EXCLUDED.sentiment,
                    topics_json = EXCLUDED.topics_json,
                    product_id = EXCLUDED.product_id,
                    source = EXCLUDED.source,
                    confidence = EXCLUDED.confidence
                """,
                [self._review_row(review) for review in reviews],
            )

    def record_prediction(self, prediction: Prediction) -> None:
        row = prediction.model_dump(mode="json")
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO predictions (
                    id, competitor_id, prediction_type, predicted_at,
                    expected_window_days, probability, evidence_json, outcome, outcome_at
                )
                VALUES (
                    %(id)s, %(competitor_id)s, %(prediction_type)s,
                    %(predicted_at)s::timestamptz, %(expected_window_days)s,
                    %(probability)s, %(evidence_json)s, %(outcome)s,
                    %(outcome_at)s::timestamptz
                )
                ON CONFLICT (id) DO UPDATE SET
                    competitor_id = EXCLUDED.competitor_id,
                    prediction_type = EXCLUDED.prediction_type,
                    predicted_at = EXCLUDED.predicted_at,
                    expected_window_days = EXCLUDED.expected_window_days,
                    probability = EXCLUDED.probability,
                    evidence_json = EXCLUDED.evidence_json,
                    outcome = EXCLUDED.outcome,
                    outcome_at = EXCLUDED.outcome_at
                """,
                {
                    **row,
                    "evidence_json": Jsonb(row["evidence_change_ids"]),
                },
            )

    def record_alert(self, alert: dict[str, object]) -> None:
        alert_id = str(alert.get("id") or alert.get("change_id") or "")
        if not alert_id:
            raise ValueError("Alert must contain id or change_id")
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alerts (id, competitor_id, change_id, payload_json, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    competitor_id = EXCLUDED.competitor_id,
                    change_id = EXCLUDED.change_id,
                    payload_json = EXCLUDED.payload_json
                """,
                (
                    alert_id,
                    str(alert.get("competitor_id", "")),
                    str(alert.get("change_id", "")),
                    Jsonb(alert),
                ),
            )

    def record_snapshot(self, competitor_id: str, snapshot: dict[str, object]) -> None:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO snapshots (id, competitor_id, captured_at, payload_json, source)
                VALUES (gen_random_uuid()::text, %s, NOW(), %s, %s)
                """,
                (competitor_id, Jsonb(snapshot), "rivalry"),
            )

    def latest_snapshot(self, competitor_id: str) -> dict[str, object]:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload_json
                FROM snapshots
                WHERE competitor_id = %s
                ORDER BY captured_at DESC, id DESC
                LIMIT 1
                """,
                (competitor_id,),
            )
            row = cur.fetchone()
        return self._json_object(row[0]) if row else {}

    def record_cost_signals(self, signals: list[CostSignal]) -> None:
        if not signals:
            return
        with self._connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO cost_signals (
                    id, product_id, type, name, before_value, after_value,
                    unit, observed_at, source, confidence
                )
                VALUES (
                    %(id)s, %(product_id)s, %(type)s, %(name)s, %(before)s,
                    %(after)s, %(unit)s, %(observed_at)s::timestamptz,
                    %(source)s, %(confidence)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    product_id = EXCLUDED.product_id,
                    type = EXCLUDED.type,
                    name = EXCLUDED.name,
                    before_value = EXCLUDED.before_value,
                    after_value = EXCLUDED.after_value,
                    unit = EXCLUDED.unit,
                    observed_at = EXCLUDED.observed_at,
                    source = EXCLUDED.source,
                    confidence = EXCLUDED.confidence
                """,
                [signal.model_dump(mode="json") for signal in signals],
            )

    def all_changes(self) -> list[Change]:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, business_id, competitor_id, type, before_json, after_json,
                       detected_at, magnitude, severity, impact_score, confidence,
                       source
                FROM changes
                ORDER BY detected_at ASC, id ASC
                """
            )
            rows = cur.fetchall()
        return [self._change_from_row(row) for row in rows]

    def all_reviews(self) -> list[Review]:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, competitor_id, rating, text, created_at, sentiment,
                       topics_json, product_id, source, confidence
                FROM reviews
                ORDER BY created_at ASC, id ASC
                """
            )
            rows = cur.fetchall()
        return [self._review_from_row(row) for row in rows]

    def all_predictions(self) -> list[Prediction]:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, competitor_id, prediction_type, predicted_at,
                       expected_window_days, probability, evidence_json,
                       outcome, outcome_at
                FROM predictions
                ORDER BY predicted_at ASC, id ASC
                """
            )
            rows = cur.fetchall()
        return [self._prediction_from_row(row) for row in rows]

    def all_cost_signals(self) -> list[CostSignal]:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, product_id, type, name, before_value, after_value,
                       unit, observed_at, source, confidence
                FROM cost_signals
                ORDER BY observed_at ASC, id ASC
                """
            )
            rows = cur.fetchall()
        return [self._cost_signal_from_row(row) for row in rows]

    def all_alerts(self) -> list[dict[str, object]]:
        with self._connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload_json
                FROM alerts
                ORDER BY created_at ASC, id ASC
                """
            )
            rows = cur.fetchall()
        return [self._json_object(row[0]) for row in rows]

    @staticmethod
    def _change_row(change: Change) -> dict[str, object]:
        row = change.model_dump(mode="json")
        return {
            "id": row["id"],
            "business_id": row["business_id"],
            "competitor_id": row["competitor_id"],
            "type": row["type"],
            "before_json": Jsonb(row["before"]),
            "after_json": Jsonb(row["after"]),
            "detected_at": row["detected_at"],
            "magnitude": row["magnitude"],
            "severity": row["severity"],
            "impact_score": row["impact_score"],
            "confidence": row["confidence"],
            "evidence_json": Jsonb([]),
            "source": row["source"],
        }

    @staticmethod
    def _review_row(review: Review) -> dict[str, object]:
        row = review.model_dump(mode="json")
        return {
            "id": row["id"],
            "competitor_id": row["competitor_id"],
            "rating": row["rating"],
            "text": row["text"],
            "created_at": row["created_at"],
            "sentiment": row["sentiment"],
            "topics_json": Jsonb(row["topics"]),
            "product_id": row["product_id"],
            "source": row["source"],
            "confidence": row["confidence"],
        }

    @staticmethod
    def _change_from_row(row: tuple[Any, ...]) -> Change:
        return Change(
            id=row[0], business_id=row[1], competitor_id=row[2], type=row[3],
            before=row[4], after=row[5], detected_at=row[6],
            magnitude=row[7], severity=row[8], impact_score=row[9],
            confidence=row[10], source=row[11],
        )

    @staticmethod
    def _review_from_row(row: tuple[Any, ...]) -> Review:
        return Review(
            id=row[0], competitor_id=row[1], rating=row[2], text=row[3],
            created_at=row[4], sentiment=row[5], topics=row[6],
            product_id=row[7], source=row[8], confidence=row[9],
        )

    @staticmethod
    def _prediction_from_row(row: tuple[Any, ...]) -> Prediction:
        return Prediction(
            id=row[0], competitor_id=row[1], prediction_type=row[2],
            predicted_at=row[3], expected_window_days=row[4], probability=row[5],
            evidence_change_ids=row[6], outcome=row[7], outcome_at=row[8],
        )

    @staticmethod
    def _cost_signal_from_row(row: tuple[Any, ...]) -> CostSignal:
        return CostSignal(
            id=row[0], product_id=row[1], type=row[2], name=row[3],
            before=row[4], after=row[5], unit=row[6] or "",
            observed_at=row[7], source=row[8], confidence=row[9],
        )

    @staticmethod
    def _json_object(value: Any) -> dict[str, object]:
        parsed = json.loads(value) if isinstance(value, str) else value
        return parsed if isinstance(parsed, dict) else {}

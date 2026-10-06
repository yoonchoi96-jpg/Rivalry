from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.jobs.models import JobType


class ActionRoute(StrEnum):
    ALERT = "alert"
    RESEARCH = "research"


@dataclass(frozen=True)
class ActionDefinition:
    name: str
    route: ActionRoute
    follow_up_job: JobType | None = None
    aliases: tuple[str, ...] = ()


class ActionRegistry:
    """Canonical mapping from decision-policy actions to safe internal routes."""

    _definitions = (
        ActionDefinition(
            name="monitor",
            route=ActionRoute.ALERT,
            aliases=("watch", "monitor_before_matching_price"),
        ),
        ActionDefinition(
            name="review",
            route=ActionRoute.ALERT,
            aliases=("human_review", "escalate"),
        ),
        ActionDefinition(
            name="investigate",
            route=ActionRoute.RESEARCH,
            follow_up_job=JobType.EXECUTE_RESEARCH,
            aliases=("verify", "research", "research_competitor", "investigate_competitor_pricing"),
        ),
        ActionDefinition(
            name="compare_price",
            route=ActionRoute.RESEARCH,
            follow_up_job=JobType.EXECUTE_RESEARCH,
            aliases=("compare_competitor_price",),
        ),
    )

    def __init__(self) -> None:
        self._by_name: dict[str, ActionDefinition] = {}
        for definition in self._definitions:
            for name in (definition.name, *definition.aliases):
                self._by_name[name] = definition

    def resolve(self, action: str) -> ActionDefinition:
        normalized = action.strip().lower()
        if not normalized:
            raise ValueError("action must not be empty")
        return self._by_name.get(
            normalized,
            ActionDefinition(name=normalized, route=ActionRoute.ALERT),
        )

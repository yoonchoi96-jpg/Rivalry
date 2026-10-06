from __future__ import annotations

from typing import Protocol

from .models import DecisionPolicy


class DecisionPolicyRepository(Protocol):
    def save(self, policy_id: str, policy: DecisionPolicy) -> DecisionPolicy: ...
    def get(self, policy_id: str) -> DecisionPolicy | None: ...
    def list(self) -> list[DecisionPolicy]: ...
    def remove(self, policy_id: str) -> bool: ...


class InMemoryDecisionPolicyRepository:
    def __init__(self) -> None:
        self._items: dict[str, DecisionPolicy] = {}

    def save(self, policy_id: str, policy: DecisionPolicy) -> DecisionPolicy:
        stored = DecisionPolicy.model_validate(policy.model_dump(mode="json"))
        stored.id = policy_id
        self._items[policy_id] = stored
        return DecisionPolicy.model_validate(stored.model_dump(mode="json"))

    def get(self, policy_id: str) -> DecisionPolicy | None:
        policy = self._items.get(policy_id)
        return None if policy is None else DecisionPolicy.model_validate(policy.model_dump(mode="json"))

    def list(self) -> list[DecisionPolicy]:
        return [
            DecisionPolicy.model_validate(policy.model_dump(mode="json"))
            for policy in self._items.values()
        ]

    def remove(self, policy_id: str) -> bool:
        return self._items.pop(policy_id, None) is not None

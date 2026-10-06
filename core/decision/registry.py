from __future__ import annotations

from .models import DecisionPolicy
from .repository import DecisionPolicyRepository, InMemoryDecisionPolicyRepository


class DecisionPolicyRegistry:
    def __init__(self, repository: DecisionPolicyRepository | None = None) -> None:
        self._repository = repository or InMemoryDecisionPolicyRepository()

    def register(self, policy_id: str, policy: DecisionPolicy) -> DecisionPolicy:
        if not policy_id.strip():
            raise ValueError("policy_id must not be empty")
        return self._repository.save(policy_id, policy)

    def get(self, policy_id: str) -> DecisionPolicy | None:
        return self._repository.get(policy_id)

    def list(self) -> list[DecisionPolicy]:
        return self._repository.list()

    def remove(self, policy_id: str) -> bool:
        return self._repository.remove(policy_id)

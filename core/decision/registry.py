from __future__ import annotations

from .models import DecisionPolicy


class DecisionPolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, DecisionPolicy] = {}

    def register(self, policy_id: str, policy: DecisionPolicy) -> DecisionPolicy:
        if not policy_id.strip():
            raise ValueError("policy_id must not be empty")
        stored = DecisionPolicy.model_validate(policy.model_dump(mode="json"))
        stored.id = policy_id
        self._policies[policy_id] = stored
        return DecisionPolicy.model_validate(stored.model_dump(mode="json"))

    def get(self, policy_id: str) -> DecisionPolicy | None:
        policy = self._policies.get(policy_id)
        return None if policy is None else DecisionPolicy.model_validate(policy.model_dump(mode="json"))

    def list(self) -> list[DecisionPolicy]:
        return [
            DecisionPolicy.model_validate(policy.model_dump(mode="json"))
            for policy in self._policies.values()
        ]

    def remove(self, policy_id: str) -> bool:
        return self._policies.pop(policy_id, None) is not None


from core.decision.models import DecisionPolicy, DecisionPolicyRule
from core.decision.registry import DecisionPolicyRegistry


def make_policy() -> DecisionPolicy:
    return DecisionPolicy(
        name="generic",
        default_action="monitor",
        default_rationale="continue observation",
        rules=[
            DecisionPolicyRule(
                factor_key="*",
                min_impact=0.5,
                max_impact=1.0,
                action="review",
                rationale="material impact requires review",
            )
        ],
    )


def test_registry_round_trips_policy_without_mutating_input():
    registry = DecisionPolicyRegistry()
    policy = make_policy()

    stored = registry.register("generic-v1", policy)
    stored.default_action = "changed"

    assert policy.default_action == "monitor"
    assert registry.get("generic-v1").default_action == "monitor"


def test_registry_lists_and_removes_policy():
    registry = DecisionPolicyRegistry()
    registry.register("generic-v1", make_policy())

    assert len(registry.list()) == 1
    assert registry.remove("generic-v1") is True
    assert registry.get("generic-v1") is None

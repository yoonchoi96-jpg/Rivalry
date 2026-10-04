from dataclasses import dataclass, field
from time import monotonic


@dataclass
class ProviderState:
    failures: int = 0
    successes: int = 0
    blocked_at: float | None = None
    last_error: str | None = None


@dataclass
class ProviderHealth:
    threshold: int = 3
    cooldown: float = 30.0
    states: dict[str, ProviderState] = field(default_factory=dict)

    def state(self, name: str) -> ProviderState:
        return self.states.setdefault(name, ProviderState())

    def allow(self, name: str) -> bool:
        state = self.state(name)
        if state.blocked_at is None:
            return True
        if monotonic() - state.blocked_at >= self.cooldown:
            state.blocked_at = None
            state.failures = 0
            return True
        return False

    def success(self, name: str) -> None:
        state = self.state(name)
        state.successes += 1
        state.failures = 0
        state.blocked_at = None
        state.last_error = None

    def failure(self, name: str, error: str) -> None:
        state = self.state(name)
        state.failures += 1
        state.last_error = error
        if state.failures >= self.threshold:
            state.blocked_at = monotonic()

    def snapshot(self) -> dict[str, dict[str, object]]:
        return {
            name: {
                "failures": s.failures,
                "successes": s.successes,
                "blocked": s.blocked_at is not None,
                "failure_rate": round(
                    s.failures / (s.failures + s.successes) * 100, 2
                ) if s.failures + s.successes else 0.0,
                "last_error": s.last_error,
            }
            for name, s in self.states.items()
        }

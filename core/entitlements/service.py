from core.plans.models import PLANS, Plan

class EntitlementService:
    def entitlements(self, plan: str):
        return PLANS[Plan(plan)]
    def competitor_limit(self, plan: str):
        return self.entitlements(plan).competitor_limit
    def can_add_competitor(self, plan: str, current_count: int):
        limit = self.competitor_limit(plan)
        return limit is None or current_count < limit
    def can_use(self, plan: str, capability: str) -> bool:
        return bool(getattr(self.entitlements(plan), capability, False))

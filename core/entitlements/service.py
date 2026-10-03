FREE_COMPETITOR_LIMIT=10
class EntitlementService:
 def competitor_limit(self,plan): return None if plan=="pro" else FREE_COMPETITOR_LIMIT
 def can_add_competitor(self,plan,current_count):
  limit=self.competitor_limit(plan); return limit is None or current_count<limit

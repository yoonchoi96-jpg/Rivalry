class UsageService:
    def __init__(self): self.ai_calls=0; self.fetches=0
    def record_ai_call(self): self.ai_calls += 1
    def record_fetch(self): self.fetches += 1
    def snapshot(self): return {"ai_calls":self.ai_calls,"fetches":self.fetches}

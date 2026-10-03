from .models import Competitor
class CompetitorService:
 def __init__(self): self._items=[]
 def list(self): return self._items
 def add(self,competitor:Competitor): self._items.append(competitor); return competitor

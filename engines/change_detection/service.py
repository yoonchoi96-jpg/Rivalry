from .models import Change
class ChangeService:
 def __init__(self): self._items=[]
 def list(self): return sorted(self._items,key=lambda x:x.impact_score,reverse=True)

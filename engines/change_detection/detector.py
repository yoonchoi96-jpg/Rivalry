from typing import Any

def detect_price_change(before: Any, after: Any):
    if before is None or after is None or before == 0: return None
    magnitude=abs((float(after)-float(before))/float(before))*100
    if magnitude == 0: return None
    return {"type":"PRICE_CHANGED","before":before,"after":after,"magnitude":round(magnitude,2)}

def detect_new_product(before: dict|None, after: dict):
    if before is None: return {"type":"NEW_PRODUCT","before":None,"after":after,"magnitude":100}
    return None

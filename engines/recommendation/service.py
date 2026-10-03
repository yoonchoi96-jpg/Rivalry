class RecommendationService:
 def recommend(self,change):
  if change.type=="PRICE_CHANGED" and change.magnitude>=5: return {"action":"monitor_before_matching_price","reason":"material price movement"}
  if change.type=="NEW_PRODUCT": return {"action":"review_product_positioning","reason":"competitor launched a new product"}
  return {"action":"monitor","reason":"insufficient signal"}

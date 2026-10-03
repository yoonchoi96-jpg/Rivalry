class RecommendationService:
    def recommend(self, change):
        if change.type=="PRICE_CHANGED" and change.magnitude>=5:
            return {"action":"monitor_before_matching_price","reason":"material price movement","confidence":85}
        if change.type=="NEW_PRODUCT":
            return {"action":"review_product_positioning","reason":"competitor launched a new product","confidence":80}
        if change.type in {"RATING_DROP","REVIEW_SPIKE"}:
            return {"action":"inspect_customer_feedback","reason":"review signal changed materially","confidence":78}
        return {"action":"monitor","reason":"insufficient signal for immediate action","confidence":60}

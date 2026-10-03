def impact_score(magnitude, frequency, market_relevance, competitor_importance, persistence):
    values=[max(0,min(100,float(v)))/100 for v in [magnitude,frequency,market_relevance,competitor_importance,persistence]]
    score=100*(values[0]*values[1]*values[2]*values[3]*values[4])**0.2
    return round(score,2)

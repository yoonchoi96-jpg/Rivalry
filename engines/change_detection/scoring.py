def impact_score(magnitude,frequency,market_relevance,competitor_importance,persistence):
 v=[max(0,min(100,float(x)))/100 for x in [magnitude,frequency,market_relevance,competitor_importance,persistence]]
 return round(100*(v[0]*v[1]*v[2]*v[3]*v[4])**0.2,2)

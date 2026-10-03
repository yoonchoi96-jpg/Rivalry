from pydantic import BaseModel,Field
class Competitor(BaseModel):
 id:str
 name:str
 platform:str
 strategic:bool=False
 similarity_score:float=Field(0,ge=0,le=100)
 market_relevance:float=Field(0,ge=0,le=100)

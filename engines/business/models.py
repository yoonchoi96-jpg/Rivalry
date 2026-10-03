from enum import StrEnum
from pydantic import BaseModel, Field

class BusinessType(StrEnum):
    RESTAURANT = "restaurant"
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    SERVICE = "service"
    OTHER = "other"

class Channel(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    OMNICHANNEL = "omnichannel"

class Business(BaseModel):
    id: str
    name: str
    country_code: str = Field(min_length=2, max_length=2)
    business_type: BusinessType
    channel: Channel
    location: str | None = None
    website_url: str | None = None
    target_customer: str | None = None
    price_positioning: str | None = None
    goal: str | None = None
    interests: list[str] = []
    source_documents: list[str] = []

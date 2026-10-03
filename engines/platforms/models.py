from enum import StrEnum
from pydantic import BaseModel

class PlatformCategory(StrEnum):
    DELIVERY = "delivery"
    MARKETPLACE = "marketplace"
    COMMERCE = "commerce"
    REVIEW = "review"
    SOCIAL = "social"
    OTHER = "other"

class PlatformConnection(BaseModel):
    id: str
    business_id: str
    country_code: str
    platform: str
    category: PlatformCategory
    status: str = "pending"
    capabilities: list[str] = []

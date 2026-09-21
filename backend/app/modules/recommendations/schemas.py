from decimal import Decimal

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    product_id: int
    product_name: str
    category_name: str
    price: Decimal
    image_url: str | None
    score: Decimal
    reason: str


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]

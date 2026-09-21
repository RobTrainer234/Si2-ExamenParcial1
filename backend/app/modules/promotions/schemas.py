from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PromotionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    discount_type: Literal["PERCENT", "FIXED"]
    discount_value: Decimal = Field(gt=0)
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_dates_and_value(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("La fecha final debe ser posterior a la fecha inicial.")
        if self.discount_type == "PERCENT" and self.discount_value > 100:
            raise ValueError("El porcentaje no puede superar 100.")
        return self


class PromotionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    discount_type: Literal["PERCENT", "FIXED"] | None = None
    discount_value: Decimal | None = Field(default=None, gt=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class PromotionProductsRequest(BaseModel):
    product_ids: list[int] = Field(min_length=1, max_length=100)


class PromotionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    discount_type: str
    discount_value: Decimal
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    product_ids: list[int]


class PromotionPage(BaseModel):
    items: list[PromotionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

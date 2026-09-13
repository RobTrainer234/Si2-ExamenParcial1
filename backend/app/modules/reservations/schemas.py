from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ReservationStatus = Literal["PENDING", "PREPARING", "READY", "ATTENDED", "CANCELLED", "EXPIRED"]


class ReservationItemRequest(BaseModel):
    product_variant_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class ReservationCreateRequest(BaseModel):
    branch_id: int = Field(gt=0)
    scheduled_for: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)
    items: list[ReservationItemRequest] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_items(self):
        variant_ids = [item.product_variant_id for item in self.items]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("Una variante no puede repetirse dentro de la reserva.")
        return self


class ReservationStatusRequest(BaseModel):
    status: ReservationStatus
    notes: str | None = Field(default=None, max_length=2000)


class ReservationItemResponse(BaseModel):
    id: int
    product_variant_id: int
    product_id: int
    product_name: str
    sku: str
    size_name: str
    color_name: str
    quantity: int
    unit_price: float


class ReservationResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    branch_id: int
    branch_name: str
    scheduled_for: datetime | None
    status: str
    notes: str | None
    expires_at: datetime | None
    created_at: datetime
    items: list[ReservationItemResponse]


class ReservationPage(BaseModel):
    items: list[ReservationResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

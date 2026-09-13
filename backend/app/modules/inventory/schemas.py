from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InventoryCreateRequest(BaseModel):
    branch_id: int = Field(gt=0)
    product_variant_id: int = Field(gt=0)
    stock_quantity: int = Field(default=0, ge=0)


class InventoryUpdateRequest(BaseModel):
    stock_quantity: int = Field(ge=0)


class InventoryResponse(BaseModel):
    id: int
    branch_id: int
    branch_name: str
    product_variant_id: int
    product_id: int
    product_name: str
    sku: str
    size_id: int
    size_name: str
    size_type: str
    size_sort_order: int
    color_id: int
    color_name: str
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    available: bool


class InventoryPage(BaseModel):
    items: list[InventoryResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class InventoryMovementCreateRequest(BaseModel):
    inventory_id: int = Field(gt=0)
    movement_type: Literal["IN", "OUT", "RETURN"]
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=2, max_length=255)


class InventoryMovementResponse(BaseModel):
    id: int
    inventory_id: int
    movement_type: str
    quantity: int
    stock_before: int
    stock_after: int
    reason: str | None
    reference_type: str | None
    reference_id: int | None
    created_by: int | None
    created_at: datetime


class InventoryMovementPage(BaseModel):
    items: list[InventoryMovementResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

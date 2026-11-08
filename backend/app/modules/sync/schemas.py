from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SyncMetadata(BaseModel):
    tenant_id: int | None = None
    tenant_name: str
    branch_id: int
    branch_name: str
    sync_timestamp: datetime
    catalog_version: str


class SyncCategoryItem(BaseModel):
    id: int
    name: str
    is_active: bool


class SyncProductItem(BaseModel):
    id: int
    category_id: int
    category_name: str
    name: str
    code: str
    slug: str
    description: str | None = None
    audience: str
    size_system: str
    price: Decimal
    image_url: str | None = None
    is_active: bool


class SyncVariantItem(BaseModel):
    id: int
    product_id: int
    sku: str
    size_id: int | None = None
    size_name: str | None = None
    size_type: str | None = None
    sort_order: int | None = None
    color_id: int | None = None
    color_name: str | None = None
    price: Decimal
    is_active: bool


class SyncInventoryItem(BaseModel):
    product_variant_id: int
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int


class SyncCatalogResponse(BaseModel):
    metadata: SyncMetadata
    categories: list[SyncCategoryItem]
    products: list[SyncProductItem]
    variants: list[SyncVariantItem]
    inventory: list[SyncInventoryItem]


class OfflineSaleItemPayload(BaseModel):
    product_variant_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class OfflineSalePayload(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    customer_name: str | None = Field(default=None, max_length=150)
    customer_nit: str | None = Field(default=None, max_length=50)
    customer_phone: str | None = Field(default=None, max_length=50)
    items: list[OfflineSaleItemPayload] = Field(min_length=1, max_length=100)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(ge=0)
    payment_method: Literal["CASH"] = "CASH"
    created_at: datetime | None = None


class OfflineReservationItemPayload(BaseModel):
    product_variant_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


class OfflineReservationPayload(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    customer_name: str | None = Field(default=None, max_length=150)
    customer_nit: str | None = Field(default=None, max_length=50)
    customer_phone: str | None = Field(default=None, max_length=50)
    items: list[OfflineReservationItemPayload] = Field(min_length=1, max_length=100)
    scheduled_for: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None


class SyncTransactionItemRequest(BaseModel):
    client_operation_id: str = Field(min_length=1, max_length=64)
    branch_id: int = Field(gt=0)
    operation_type: Literal["SALE", "RESERVATION"]
    sale_payload: OfflineSalePayload | None = None
    reservation_payload: OfflineReservationPayload | None = None


class SyncTransactionBatchRequest(BaseModel):
    operations: list[SyncTransactionItemRequest] = Field(min_length=1, max_length=200)


class SyncConflictDetail(BaseModel):
    code: str
    message: str
    variant_id: int | None = None
    sku: str | None = None
    requested_quantity: int | None = None
    available_quantity: int | None = None


class SyncTransactionItemResult(BaseModel):
    client_operation_id: str
    operation_type: str
    status: Literal["CONFIRMED", "CONFLICT", "REJECTED"]
    sale_id: int | None = None
    order_number: str | None = None
    reservation_id: int | None = None
    conflict_detail: SyncConflictDetail | None = None
    processed_at: datetime


class SyncTransactionBatchResponse(BaseModel):
    processed_count: int
    confirmed_count: int
    conflict_count: int
    results: list[SyncTransactionItemResult]


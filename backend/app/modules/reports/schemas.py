from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SalesByBranchItem(BaseModel):
    branch_id: int | None
    branch_name: str
    sales_count: int
    total: Decimal


class TopProductItem(BaseModel):
    product_id: int
    product_name: str
    units_sold: int
    revenue: Decimal


class LowStockItem(BaseModel):
    inventory_id: int
    branch_id: int
    branch_name: str
    product_id: int
    product_name: str
    sku: str
    available_quantity: int


class ReservationStatusItem(BaseModel):
    status: str
    count: int


class SalesByChannelItem(BaseModel):
    channel: str
    sales_count: int
    total: Decimal


class RevenueSummary(BaseModel):
    sales_count: int
    subtotal: Decimal
    discount: Decimal
    total: Decimal


class DashboardResponse(BaseModel):
    revenue: RevenueSummary
    sales_by_branch: list[SalesByBranchItem]
    top_products: list[TopProductItem]
    low_stock: list[LowStockItem]
    reservations: list[ReservationStatusItem]
    sales_by_channel: list[SalesByChannelItem]


class ReportFilters(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    branch_id: int | None = None


class ReportSnapshot(DashboardResponse):
    filters: ReportFilters


ReportAssistantIntentKind = Literal["dashboard", "top_products", "sales_by_branch", "inventory", "reservations"]
ReportAssistantProvider = Literal["gemini", "openai", "local"]


class ReportAssistantRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    date_from: datetime | None = None
    date_to: datetime | None = None
    branch_id: int | None = None


class ReportAssistantIntent(BaseModel):
    kind: ReportAssistantIntentKind
    filters: ReportFilters = Field(default_factory=ReportFilters)
    reasoning: str = ""


class ReportAssistantResponse(BaseModel):
    intent: ReportAssistantIntent
    filters: ReportFilters
    data: DashboardResponse | list[TopProductItem] | list[SalesByBranchItem] | list[LowStockItem] | list[ReservationStatusItem]
    narrative: str
    provider: ReportAssistantProvider
    fallback_used: bool

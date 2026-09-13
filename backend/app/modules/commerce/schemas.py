from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CartItemRequest(BaseModel):
    product_variant_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: int
    product_variant_id: int
    product_id: int
    product_name: str
    sku: str
    size_name: str
    color_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    available_quantity: int


class CartResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    items: list[CartItemResponse]
    subtotal: Decimal
    total: Decimal
    updated_at: datetime


class SaleItemRequest(BaseModel):
    product_variant_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class PhysicalSaleRequest(BaseModel):
    branch_id: int = Field(gt=0)
    customer_id: int | None = Field(default=None, gt=0)
    items: list[SaleItemRequest] = Field(min_length=1, max_length=100)
    discount: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode="after")
    def unique_items(self):
        ids = [item.product_variant_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Una variante no puede repetirse en una venta.")
        return self


class DigitalPurchaseRequest(BaseModel):
    branch_id: int = Field(gt=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)


class SaleItemResponse(BaseModel):
    id: int
    product_variant_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    discount: Decimal
    line_total: Decimal


class PaymentResponse(BaseModel):
    id: int
    sale_id: int
    method: str
    provider: str | None
    transaction_reference: str | None
    status: str
    amount: Decimal
    paid_at: datetime | None


class SaleResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int | None
    branch_id: int | None
    cashier_id: int | None
    channel: str
    status: str
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    created_at: datetime
    items: list[SaleItemResponse]
    payments: list[PaymentResponse]


class CashPaymentRequest(BaseModel):
    method: Literal["CASH", "CARD", "QR"]
    amount: Decimal = Field(gt=0)
    transaction_reference: str | None = Field(default=None, max_length=150)


class ElectronicPaymentRequest(BaseModel):
    sale_id: int = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=100)
    method: Literal["CARD", "QR", "BANK_TRANSFER"] = "CARD"


class ElectronicNotificationRequest(BaseModel):
    transaction_reference: str = Field(min_length=3, max_length=150)
    status: Literal["APPROVED", "REJECTED", "CANCELLED"]
    amount: Decimal = Field(gt=0)

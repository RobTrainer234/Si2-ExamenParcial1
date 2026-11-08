from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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
    discount: Decimal = Decimal("0")
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


class ShippingDetailsRequest(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=120)
    recipient_ci: str = Field(min_length=1, max_length=30)
    recipient_phone: str = Field(min_length=1, max_length=30)
    department_or_city: str = Field(min_length=1, max_length=100)
    zone: str = Field(min_length=1, max_length=120)
    street: str = Field(min_length=1, max_length=150)
    house_number: str = Field(min_length=1, max_length=50)
    reference: str = Field(min_length=1, max_length=255)

    @field_validator("recipient_name", "recipient_ci", "recipient_phone", "department_or_city", "zone", "street", "house_number", "reference")
    @classmethod
    def not_blank(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("El campo es obligatorio.")
        return clean


class DigitalPurchaseRequest(BaseModel):
    branch_id: int = Field(gt=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    fulfillment_type: Literal["PICKUP", "DELIVERY"] = "PICKUP"
    shipping_details: ShippingDetailsRequest | None = None

    @model_validator(mode="after")
    def delivery_requires_shipping_details(self):
        if self.fulfillment_type == "DELIVERY" and self.shipping_details is None:
            raise ValueError("Los datos de envío son obligatorios para delivery.")
        return self


class ShippingDetailsResponse(BaseModel):
    recipient_name: str
    recipient_ci: str
    recipient_phone: str
    department_or_city: str
    zone: str
    street: str
    house_number: str
    reference: str


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
    received_amount: Decimal | None = None
    change_amount: Decimal | None = None
    paid_at: datetime | None


class SaleResponse(BaseModel):
    id: int
    credit_note_code: str | None = None
    return_id: int | None = None
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
    fulfillment_type: Literal["PICKUP", "DELIVERY"] = "PICKUP"
    shipping_details: ShippingDetailsResponse | None = None
    items: list[SaleItemResponse]
    payments: list[PaymentResponse]


class SaleReturnResponse(SaleResponse):
    return_id: int
    credit_note_code: str
    credit_note_amount: Decimal


class CreditNoteSettlementResponse(SaleResponse):
    redemption_id: int
    applied_amount: Decimal
    post_redemption_balance: Decimal
    cash_change: Decimal


class PurchaseHistoryPage(BaseModel):
    items: list[SaleResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class CashPaymentRequest(BaseModel):
    method: Literal["CASH", "CARD", "QR"]
    amount: Decimal = Field(gt=0)
    transaction_reference: str | None = Field(default=None, max_length=150)


class CreditNoteLookupRequest(BaseModel):
    credit_note_code: str = Field(min_length=1, max_length=50)
    customer_id: int = Field(gt=0)
    branch_id: int = Field(gt=0)


class CreditNoteLookupResponse(BaseModel):
    available_balance: Decimal
    customer_id: int
    expires_at: datetime | None = None


class CreditNoteSettlementRequest(BaseModel):
    credit_note_code: str = Field(min_length=1, max_length=50)
    idempotency_key: str = Field(min_length=8, max_length=100)
    method: Literal["CASH", "CARD", "QR"] | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    transaction_reference: str | None = Field(default=None, max_length=150)


class ElectronicPaymentRequest(BaseModel):
    sale_id: int = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=100)
    method: Literal["CARD", "QR", "BANK_TRANSFER"] = "CARD"


class ElectronicNotificationRequest(BaseModel):
    transaction_reference: str = Field(min_length=3, max_length=150)
    status: Literal["APPROVED", "REJECTED", "CANCELLED"]
    amount: Decimal = Field(gt=0)


class ReturnLineRequest(BaseModel):
    sale_item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    condition: Literal["SELLABLE", "DAMAGED"] = "SELLABLE"


class SaleReturnRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255, description="Motivo de la devolución de la venta")
    items: list[ReturnLineRequest] | None = Field(default=None, min_length=1, max_length=100)
    beneficiary_customer_id: int | None = Field(default=None, gt=0)
    idempotency_key: str = Field(min_length=8, max_length=100)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("El motivo es obligatorio.")
        return clean

    @model_validator(mode="after")
    def unique_sale_items(self):
        if self.items is not None:
            ids = [item.sale_item_id for item in self.items]
            if len(ids) != len(set(ids)):
                raise ValueError("Una línea de venta no puede repetirse en una devolución.")
        return self


class StripePaymentIntentRequest(BaseModel):
    sale_id: int = Field(gt=0)
    idempotency_key: str = Field(min_length=5, max_length=100)
    method: Literal["CARD"] = "CARD"


class StripePaymentIntentResponse(BaseModel):
    payment_id: int
    sale_id: int
    provider: Literal["STRIPE"] = "STRIPE"
    payment_intent_id: str
    client_secret: str
    amount: Decimal
    currency: str
    status: Literal["PENDING", "APPROVED", "FAILED", "CANCELLED"] = "PENDING"


class StripePaymentConfirmRequest(BaseModel):
    payment_intent_id: str = Field(min_length=3, max_length=150)


class QRPaymentGenerateRequest(BaseModel):
    sale_id: int = Field(gt=0)
    client_base_url: str | None = None


class QRPaymentResponse(BaseModel):
    payment_id: int
    sale_id: int
    order_number: str
    amount: Decimal
    currency: str = "BOB"
    qr_data: str
    qr_image_url: str
    business_name: str
    nit: str
    bank_name: str
    transaction_reference: str
    expires_at: datetime
    status: str = "PENDING"


class QRPaymentSimulateRequest(BaseModel):
    transaction_reference: str = Field(min_length=3, max_length=150)
    amount: Decimal = Field(gt=0)


class QRTransferConfirmRequest(BaseModel):
    transaction_reference: str = Field(min_length=3, max_length=150)
    amount: Decimal = Field(gt=0)


class QRPaymentStatusResponse(BaseModel):
    transaction_reference: str
    sale_id: int
    order_number: str
    amount: Decimal
    currency: str = "BOB"
    status: str
    is_confirmed: bool


class ExchangeQuoteRequest(BaseModel):
    returned_variant_id: int = Field(gt=0)
    returned_quantity: int = Field(default=1, gt=0)
    new_variant_id: int = Field(gt=0)
    new_quantity: int = Field(default=1, gt=0)


class ItemExchangeRequest(ExchangeQuoteRequest):
    quote_fingerprint: str = Field(min_length=16, max_length=256)
    quote_expires_at: datetime
    idempotency_key: str = Field(min_length=8, max_length=100)
    cash_tendered: Decimal | None = Field(default=None, gt=0)
    cashier_confirmed: bool = False
    reason: str | None = Field(default=None, max_length=255)
    item_condition: str | None = Field(default="EXCELLENT", max_length=50)
    inspection_checklist: list[str] | None = Field(default=None)
    condition_notes: str | None = Field(default=None, max_length=255)


class ReturnLookupItemResponse(BaseModel):
    id: int
    variant_id: int
    name: str
    sku: str
    purchased_quantity: int
    net_paid_line_total: Decimal
    remaining_returnable_quantity: int


class ReturnLookupResponse(BaseModel):
    sale_id: int
    order_number: str
    sale_date: datetime
    branch_id: int
    status: str
    customer_id: int | None = None
    items: list[ReturnLookupItemResponse]


class ExchangeLookupItemResponse(BaseModel):
    id: int
    variant_id: int
    name: str
    sku: str
    purchased_quantity: int
    net_paid_line_total: Decimal
    remaining_exchangeable_quantity: int
    category_name: str | None = None
    exchange_days: int = 30
    is_exchangeable: bool = True
    policy_note: str | None = None


class ExchangeLookupResponse(BaseModel):
    sale_id: int
    order_number: str
    sale_date: datetime
    branch_id: int
    status: str
    store_policy_days: int = 30
    days_elapsed: int = 0
    is_within_policy: bool = True
    policy_summary: str = "Política general de la tienda: 30 días para prendas estándar."
    items: list[ExchangeLookupItemResponse]


class ExchangeQuoteResponse(BaseModel):
    sale_id: int
    sale_item_id: int
    returned_variant_id: int
    returned_quantity: int
    new_variant_id: int
    new_quantity: int
    returned_value: Decimal
    replacement_unit_price: Decimal
    delivered_value: Decimal
    difference: Decimal
    cash_settlement_eligible: bool
    available_stock: int
    reserved_stock: int
    expires_at: datetime
    quote_fingerprint: str


class ItemExchangeResponse(BaseModel):
    sale_id: int
    order_number: str
    returned_variant_id: int
    returned_quantity: int
    new_variant_id: int
    new_quantity: int
    status: str
    quarantine_id: int | None = None
    quarantine_status: str | None = None
    item_condition: str | None = None
    inspection_summary: str | None = None
    returned_value: Decimal = Decimal("0.00")
    delivered_value: Decimal = Decimal("0.00")
    difference: Decimal = Decimal("0.00")
    cash_tendered: Decimal | None = None
    cash_change: Decimal | None = None
    cash_refunded: Decimal | None = None
    exchanged_at: datetime

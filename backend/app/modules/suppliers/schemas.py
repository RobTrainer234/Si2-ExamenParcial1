from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


SupplyStatus = Literal["AVAILABLE", "LIMITED", "OUT_OF_STOCK", "UPCOMING"]


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class SupplierCreateRequest(BaseModel):
    trade_name: str = Field(min_length=2, max_length=150)
    legal_name: str | None = Field(default=None, max_length=200)
    tax_id: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=30)
    address: str | None = Field(default=None, max_length=255)

    _clean_trade_name = field_validator("trade_name")(lambda value: value.strip())
    _clean_legal_name = field_validator("legal_name", "tax_id", "address")(  # type: ignore[misc]
        _normalize_optional,
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized


class SupplierUpdateRequest(BaseModel):
    trade_name: str | None = Field(default=None, min_length=2, max_length=150)
    legal_name: str | None = Field(default=None, max_length=200)
    tax_id: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=30)
    address: str | None = Field(default=None, max_length=255)

    _clean_trade_name = field_validator("trade_name")(lambda value: value.strip() if value is not None else None)
    _clean_legal_name = field_validator("legal_name", "tax_id", "address")(  # type: ignore[misc]
        _normalize_optional,
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized


class SupplierResponse(BaseModel):
    id: int
    trade_name: str
    legal_name: str | None
    tax_id: str | None
    email: EmailStr | None
    phone: str | None
    address: str | None
    is_active: bool
    product_ids: list[int] = Field(default_factory=list)


class SupplierPage(BaseModel):
    items: list[SupplierResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class SupplierPortalProduct(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool


class SupplierPortalResponse(BaseModel):
    supplier_id: int
    trade_name: str
    products: list[SupplierPortalProduct]


class SupplyOfferCreateRequest(BaseModel):
    product_variant_id: int = Field(gt=0)
    season_id: int = Field(gt=0)
    collection_id: int | None = Field(default=None, gt=0)
    status: SupplyStatus = "AVAILABLE"
    available_quantity: int = Field(default=0, ge=0)
    expected_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class SupplyOfferAdminUpdateRequest(BaseModel):
    product_variant_id: int | None = Field(default=None, gt=0)
    season_id: int | None = Field(default=None, gt=0)
    collection_id: int | None = Field(default=None, gt=0)
    status: SupplyStatus | None = None
    available_quantity: int | None = Field(default=None, ge=0)
    expected_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class SupplyOfferSupplierUpdateRequest(BaseModel):
    status: SupplyStatus | None = None
    available_quantity: int | None = Field(default=None, ge=0)
    expected_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class SupplyOfferResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    product_id: int
    product_name: str
    product_variant_id: int
    sku: str
    size_name: str
    color_name: str
    season_id: int
    season_name: str
    collection_id: int | None
    collection_name: str | None
    status: SupplyStatus
    available_quantity: int
    expected_date: date | None
    notes: str | None
    is_active: bool

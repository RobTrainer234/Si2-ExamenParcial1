from pydantic import BaseModel, EmailStr, Field, field_validator


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


class SupplierPage(BaseModel):
    items: list[SupplierResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

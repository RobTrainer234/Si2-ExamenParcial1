from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    price_monthly: float = 0.0
    price_annual: float = 0.0
    currency: str = "BOB"
    max_active_branches: int
    generative_reports_enabled: bool
    is_active: bool


class SubscriptionPlanCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=100)
    price_monthly: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    price_annual: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field(default="BOB", min_length=2, max_length=10)
    max_active_branches: int = Field(ge=1, le=500)
    generative_reports_enabled: bool = False
    is_active: bool = True


class SubscriptionPlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    price_monthly: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    price_annual: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    currency: str | None = Field(default=None, min_length=2, max_length=10)
    max_active_branches: int | None = Field(default=None, ge=1, le=500)
    generative_reports_enabled: bool | None = None
    is_active: bool | None = None


class SubscriptionPlanPage(BaseModel):
    items: list[SubscriptionPlanResponse]
    total: int


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    plan: SubscriptionPlanResponse
    status: str
    valid_from: datetime
    valid_until: datetime | None = None
    paused_at: datetime | None = None


class SubscriptionHistoryPage(BaseModel):
    items: list[SubscriptionResponse]
    total: int


class EmailVerificationStartRequest(BaseModel):
    email: EmailStr


class EmailVerificationStartResponse(BaseModel):
    accepted: bool = True
    email_sent: bool = False


class EmailVerificationVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class EmailVerificationVerifyResponse(BaseModel):
    verified: bool = True
    checkout_capability: str


class PaidCheckoutRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=150)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    plan_code: str = Field(min_length=2, max_length=32)
    billing_interval: Literal["monthly", "annual"]
    checkout_capability: str = Field(min_length=14, max_length=256)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if (
            not any(char.isupper() for char in value)
            or not any(char.islower() for char in value)
            or not any(char.isdigit() for char in value)
            or not any(not char.isalnum() for char in value)
        ):
            raise ValueError("La contraseña debe incluir mayúsculas, minúsculas, números y un carácter especial")
        return value


class PaidCheckoutResponse(BaseModel):
    session_id: str
    session_url: str


class PaidCheckoutStatusResponse(BaseModel):
    status: Literal["PENDING", "CHECKOUT_CREATED", "COMPLETED", "EXPIRED", "EMAIL_CONFLICT", "ERROR"]


class TrialSignupRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=150)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if (
            not any(char.isupper() for char in value)
            or not any(char.islower() for char in value)
            or not any(char.isdigit() for char in value)
            or not any(not char.isalnum() for char in value)
        ):
            raise ValueError("La contraseña debe incluir mayúsculas, minúsculas, números y un carácter especial")
        return value


class ReactivationRequestPayload(BaseModel):
    plan_code: str = Field(default="BASIC", min_length=2, max_length=50)
    notes: str | None = Field(default=None, max_length=500)


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    plan_code: str = Field(default="BASIC", min_length=2, max_length=50)
    admin_email: EmailStr | None = None
    admin_password: str | None = Field(default=None, min_length=8)
    admin_first_name: str | None = Field(default=None, max_length=100)
    admin_last_name: str | None = Field(default=None, max_length=100)
    admin_phone: str | None = Field(default=None, max_length=30)


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    created_at: datetime
    active_subscription: SubscriptionResponse | None = None
    is_trial: bool = False
    is_expired: bool = False
    is_cancelled: bool = False
    cancellation_reason: str | None = None
    reactivation_requested: bool = False
    requested_plan_code: str | None = None


class TenantPage(BaseModel):
    items: list[TenantResponse]
    total: int


class SubscriptionChangeRequest(BaseModel):
    plan_code: str = Field(min_length=2, max_length=50)
    valid_until: datetime | None = None


class SubscriptionCancelRequest(BaseModel):
    reason: Literal["PRICE", "FEATURES", "PAUSE", "ANOTHER_SOFTWARE", "NOT_USING", "OTHER"] = "OTHER"
    feedback: str | None = Field(default=None, max_length=500)
    immediate: bool = False


class TenantStatusUpdateRequest(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED", "INACTIVE"]


class SubscriptionCurrentResponse(BaseModel):
    tenant_id: int
    tenant_name: str
    tenant_status: str
    subscription: SubscriptionResponse | None = None
    plan: SubscriptionPlanResponse | None = None
    max_active_branches: int = 1
    generative_reports_enabled: bool = False
    active_branch_count: int = 0
    is_trial: bool = False
    is_expired: bool = False
    is_cancelled: bool = False
    cancellation_reason: str | None = None
    cancellation_effective_at: datetime | None = None
    read_only_mode: bool = False
    is_paused: bool = False
    days_remaining: int | None = None
    retention_days_remaining: int | None = None
    email_verified: bool = True
    reactivation_requested: bool = False
    requested_plan_code: str | None = None


class TenantExportResponse(BaseModel):
    tenant: dict[str, Any]
    subscription: dict[str, Any] | None = None
    retention_days_remaining: int | None = None
    exported_at: datetime
    branches: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    products: list[dict[str, Any]]


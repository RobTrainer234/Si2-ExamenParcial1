from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class CityCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class CityUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)


class CityResponse(BaseModel):
    id: int
    name: str
    is_active: bool


class CityPage(BaseModel):
    items: list[CityResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class BranchCreateRequest(BaseModel):
    city_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=3, max_length=255)
    phone: str = Field(min_length=7, max_length=30)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized


class BranchUpdateRequest(BaseModel):
    city_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, min_length=7, max_length=30)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized


class BranchResponse(BaseModel):
    id: int
    city_id: int
    city_name: str
    name: str
    address: str
    phone: str
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool


class BranchPage(BaseModel):
    items: list[BranchResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

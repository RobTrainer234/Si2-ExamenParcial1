from typing import Literal

from pydantic import BaseModel, Field, field_validator


def clean_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("El nombre es obligatorio")
    return normalized


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    _clean_name = field_validator("name")(clean_name)


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    _clean_name = field_validator("name")(clean_name)


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool


class SizeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    size_type: Literal["ALPHA", "NUMERIC", "ONE_SIZE"] = "ALPHA"
    sort_order: int = Field(default=0, ge=0, le=9999)

    _clean_name = field_validator("name")(clean_name)


class SizeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=20)
    size_type: Literal["ALPHA", "NUMERIC", "ONE_SIZE"] | None = None
    sort_order: int | None = Field(default=None, ge=0, le=9999)

    _clean_name = field_validator("name")(clean_name)


class SizeResponse(BaseModel):
    id: int
    name: str
    size_type: str
    sort_order: int
    is_active: bool


class ColorCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    hex_code: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

    _clean_name = field_validator("name")(clean_name)


class ColorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    hex_code: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

    _clean_name = field_validator("name")(clean_name)


class ColorResponse(BaseModel):
    id: int
    name: str
    hex_code: str | None
    is_active: bool


class MasterPage[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int

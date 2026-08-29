from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class VariantInput(BaseModel):
    size_id: int = Field(gt=0)
    color_id: int = Field(gt=0)
    sku: str = Field(min_length=2, max_length=80)
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        return value.strip().upper()


class ImageInput(BaseModel):
    image_url: AnyHttpUrl
    is_primary: bool = False
    sort_order: int = Field(default=0, ge=0)


class ProductCreateRequest(BaseModel):
    category_id: int = Field(gt=0)
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=180)
    slug: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    supplier_ids: list[int] = Field(default_factory=list)
    variants: list[VariantInput] = Field(default_factory=list)
    images: list[ImageInput] = Field(default_factory=list)

    @field_validator("code", "name", "slug")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()


class ProductUpdateRequest(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    supplier_ids: list[int] | None = None

    @field_validator("code", "name", "slug")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class VariantResponse(BaseModel):
    id: int
    size_id: int
    size_name: str
    color_id: int
    color_name: str
    sku: str
    is_active: bool


class ImageResponse(BaseModel):
    id: int
    image_url: AnyHttpUrl
    is_primary: bool
    sort_order: int


class ProductResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    code: str
    name: str
    slug: str
    description: str | None
    price: Decimal
    is_active: bool
    variants: list[VariantResponse]
    images: list[ImageResponse]
    supplier_ids: list[int]


class ProductSummary(BaseModel):
    id: int
    category_id: int
    category_name: str
    code: str
    name: str
    slug: str
    price: Decimal
    is_active: bool


class ProductPage(BaseModel):
    items: list[ProductSummary]
    page: int
    page_size: int
    total: int
    total_pages: int

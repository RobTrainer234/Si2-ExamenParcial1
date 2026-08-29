from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel


class CatalogItem(BaseModel):
    id: int
    category_id: int
    category_name: str
    code: str
    name: str
    slug: str
    price: Decimal
    image_url: AnyHttpUrl | None


class CatalogPage(BaseModel):
    items: list[CatalogItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class CatalogFilterOption(BaseModel):
    id: int
    name: str


class CatalogFilters(BaseModel):
    categories: list[CatalogFilterOption]
    sizes: list[CatalogFilterOption]
    colors: list[CatalogFilterOption]
    branches: list[CatalogFilterOption]


class CatalogVariant(BaseModel):
    id: int
    size_id: int
    size_name: str
    color_id: int
    color_name: str
    sku: str


class CatalogImage(BaseModel):
    image_url: AnyHttpUrl
    is_primary: bool
    sort_order: int


class CatalogDetail(BaseModel):
    id: int
    category_id: int
    category_name: str
    code: str
    name: str
    slug: str
    description: str | None
    price: Decimal
    images: list[CatalogImage]
    variants: list[CatalogVariant]


class AvailabilityItem(BaseModel):
    branch_id: int
    branch_name: str
    city_name: str
    address: str
    available: bool
    stock: int

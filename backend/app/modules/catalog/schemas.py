from decimal import Decimal

from pydantic import BaseModel


class CatalogItem(BaseModel):
    id: int
    category_id: int
    category_name: str
    audience: str
    code: str
    name: str
    slug: str
    price: Decimal
    image_url: str | None


class CatalogPage(BaseModel):
    items: list[CatalogItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class CatalogFilterOption(BaseModel):
    id: int
    name: str
    hex_code: str | None = None
    size_type: str | None = None
    sort_order: int | None = None


class AudienceOption(BaseModel):
    code: str
    name: str
    product_count: int


class CatalogFilters(BaseModel):
    categories: list[CatalogFilterOption]
    sizes: list[CatalogFilterOption]
    colors: list[CatalogFilterOption]
    branches: list[CatalogFilterOption]
    audiences: list["AudienceOption"]


class NavigationCollection(BaseModel):
    id: int
    name: str
    product_count: int


class NavigationSeason(BaseModel):
    id: int
    name: str
    collections: list[NavigationCollection]


class CatalogNavigation(BaseModel):
    audiences: list[AudienceOption]
    categories: list[CatalogFilterOption]
    seasons: list[NavigationSeason]
    branches: list[CatalogFilterOption]


class CatalogVariant(BaseModel):
    id: int
    size_id: int
    size_name: str
    color_id: int
    color_name: str
    sku: str
    size_type: str
    sort_order: int
    stock_total: int
    available: bool


class CatalogImage(BaseModel):
    image_url: str
    is_primary: bool
    sort_order: int


class CatalogDetail(BaseModel):
    id: int
    category_id: int
    category_name: str
    audience: str
    size_system: str
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

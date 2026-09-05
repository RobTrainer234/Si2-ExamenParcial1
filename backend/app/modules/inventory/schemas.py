from pydantic import BaseModel, Field


class InventoryCreateRequest(BaseModel):
    branch_id: int = Field(gt=0)
    product_variant_id: int = Field(gt=0)
    stock_quantity: int = Field(default=0, ge=0)


class InventoryUpdateRequest(BaseModel):
    stock_quantity: int = Field(ge=0)


class InventoryResponse(BaseModel):
    id: int
    branch_id: int
    branch_name: str
    product_variant_id: int
    product_id: int
    product_name: str
    sku: str
    size_id: int
    size_name: str
    size_type: str
    size_sort_order: int
    color_id: int
    color_name: str
    stock_quantity: int
    available: bool


class InventoryPage(BaseModel):
    items: list[InventoryResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

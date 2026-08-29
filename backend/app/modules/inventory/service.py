from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.models import Branch, Inventory, ProductVariant
from app.modules.inventory.schemas import InventoryCreateRequest, InventoryUpdateRequest


def _error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _inventory_query():
    return select(Inventory).options(
        joinedload(Inventory.branch),
        joinedload(Inventory.product_variant).joinedload(ProductVariant.product),
        joinedload(Inventory.product_variant).joinedload(ProductVariant.size),
        joinedload(Inventory.product_variant).joinedload(ProductVariant.color),
    )


def serialize_inventory(item: Inventory) -> dict[str, object]:
    variant = item.product_variant
    return {
        "id": item.id,
        "branch_id": item.branch_id,
        "branch_name": item.branch.name,
        "product_variant_id": item.product_variant_id,
        "product_id": variant.product_id,
        "product_name": variant.product.name,
        "sku": variant.sku,
        "size_id": variant.size_id,
        "size_name": variant.size.name,
        "color_id": variant.color_id,
        "color_name": variant.color.name,
        "stock_quantity": item.stock_quantity,
        "available": item.stock_quantity > 0,
    }


def get_inventory(db: Session, inventory_id: int) -> Inventory:
    item = db.scalar(_inventory_query().where(Inventory.id == inventory_id))
    if item is None:
        raise _error("INVENTORY_NOT_FOUND", "Registro de inventario no encontrado.", status.HTTP_404_NOT_FOUND)
    return item


def _validate_references(db: Session, branch_id: int, variant_id: int) -> ProductVariant:
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.is_active.is_(True)))
    if branch is None:
        raise _error("BRANCH_NOT_FOUND_OR_INACTIVE", "La sucursal no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == variant_id, ProductVariant.is_active.is_(True)))
    if variant is None or not variant.product.is_active:
        raise _error("VARIANT_NOT_FOUND_OR_INACTIVE", "La variante no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    return variant


def list_inventory(db: Session, page: int, page_size: int, branch_id: int | None, product_id: int | None) -> dict[str, object]:
    statement = _inventory_query().join(ProductVariant, Inventory.product_variant_id == ProductVariant.id).order_by(Inventory.id.desc())
    count_statement = select(func.count(Inventory.id)).join(ProductVariant, Inventory.product_variant_id == ProductVariant.id)
    if branch_id is not None:
        statement = statement.where(Inventory.branch_id == branch_id)
        count_statement = count_statement.where(Inventory.branch_id == branch_id)
    if product_id is not None:
        statement = statement.where(ProductVariant.product_id == product_id)
        count_statement = count_statement.where(ProductVariant.product_id == product_id)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_inventory(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def create_inventory(db: Session, data: InventoryCreateRequest) -> Inventory:
    _validate_references(db, data.branch_id, data.product_variant_id)
    if db.scalar(select(Inventory.id).where(Inventory.branch_id == data.branch_id, Inventory.product_variant_id == data.product_variant_id)):
        raise _error("INVENTORY_ALREADY_EXISTS", "Ya existe inventario para la sucursal y variante indicadas.", status.HTTP_409_CONFLICT)
    item = Inventory(**data.model_dump())
    db.add(item)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _error("INVENTORY_ALREADY_EXISTS", "Ya existe inventario para la sucursal y variante indicadas.", status.HTTP_409_CONFLICT) from exc
    return get_inventory(db, item.id)


def update_inventory(db: Session, item: Inventory, data: InventoryUpdateRequest) -> Inventory:
    item.stock_quantity = data.stock_quantity
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _error("INVALID_STOCK", "La cantidad de stock no es válida.", status.HTTP_400_BAD_REQUEST) from exc
    return get_inventory(db, item.id)

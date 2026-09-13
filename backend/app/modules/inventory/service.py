from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.models import Branch, Inventory, InventoryMovement, ProductVariant, User
from app.modules.inventory.schemas import InventoryCreateRequest, InventoryMovementCreateRequest, InventoryUpdateRequest


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
        "size_type": variant.size.size_type,
        "size_sort_order": variant.size.sort_order,
        "color_id": variant.color_id,
        "color_name": variant.color.name,
        "stock_quantity": item.stock_quantity,
        "reserved_quantity": item.reserved_quantity,
        "available_quantity": item.stock_quantity - item.reserved_quantity,
        "available": item.stock_quantity - item.reserved_quantity > 0,
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


def list_inventory(db: Session, page: int, page_size: int, branch_id: int | None, product_id: int | None, allowed_branch_ids: set[int] | None = None) -> dict[str, object]:
    statement = _inventory_query().join(ProductVariant, Inventory.product_variant_id == ProductVariant.id).order_by(Inventory.id.desc())
    count_statement = select(func.count(Inventory.id)).join(ProductVariant, Inventory.product_variant_id == ProductVariant.id)
    if branch_id is not None:
        statement = statement.where(Inventory.branch_id == branch_id)
        count_statement = count_statement.where(Inventory.branch_id == branch_id)
    if allowed_branch_ids is not None:
        statement = statement.where(Inventory.branch_id.in_(allowed_branch_ids))
        count_statement = count_statement.where(Inventory.branch_id.in_(allowed_branch_ids))
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


def update_inventory(db: Session, item: Inventory, data: InventoryUpdateRequest, user: User | None = None) -> Inventory:
    previous_stock = item.stock_quantity
    if data.stock_quantity < item.reserved_quantity:
        raise _error("STOCK_BELOW_RESERVED", "El stock físico no puede ser menor que el stock reservado.", status.HTTP_400_BAD_REQUEST)
    item.stock_quantity = data.stock_quantity
    difference = data.stock_quantity - previous_stock
    if difference:
        db.add(InventoryMovement(
            inventory_id=item.id,
            quantity=abs(difference),
            stock_before=previous_stock,
            stock_after=data.stock_quantity,
            movement_type="IN" if difference > 0 else "OUT",
            reason="Ajuste manual de inventario",
            created_by=user.id if user else None,
        ))
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _error("INVALID_STOCK", "La cantidad de stock no es válida.", status.HTTP_400_BAD_REQUEST) from exc
    return get_inventory(db, item.id)


def get_locked_inventory(db: Session, inventory_id: int) -> Inventory:
    item = db.scalar(_inventory_query().where(Inventory.id == inventory_id).with_for_update())
    if item is None:
        raise _error("INVENTORY_NOT_FOUND", "Registro de inventario no encontrado.", status.HTTP_404_NOT_FOUND)
    return item


def apply_movement(
    db: Session,
    inventory_id: int,
    movement_type: str,
    quantity: int,
    reason: str,
    user: User | None = None,
    *,
    reference_type: str | None = None,
    reference_id: int | None = None,
) -> InventoryMovement:
    item = get_locked_inventory(db, inventory_id)
    before = item.stock_quantity
    increases_stock = movement_type in {"IN", "RETURN"}
    after = before + quantity if increases_stock else before - quantity
    if after < item.reserved_quantity or after < 0:
        raise _error("INSUFFICIENT_STOCK", "El movimiento supera el stock disponible.", status.HTTP_409_CONFLICT)
    item.stock_quantity = after
    movement = InventoryMovement(
        inventory_id=item.id,
        movement_type=movement_type,
        quantity=quantity,
        stock_before=before,
        stock_after=after,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=user.id if user else None,
    )
    db.add(movement)
    db.flush()
    return movement


def list_movements(db: Session, page: int, page_size: int, inventory_id: int | None, movement_type: str | None) -> dict[str, object]:
    statement = select(InventoryMovement).order_by(InventoryMovement.id.desc())
    count_statement = select(func.count(InventoryMovement.id))
    if inventory_id is not None:
        statement = statement.where(InventoryMovement.inventory_id == inventory_id)
        count_statement = count_statement.where(InventoryMovement.inventory_id == inventory_id)
    if movement_type is not None:
        statement = statement.where(InventoryMovement.movement_type == movement_type)
        count_statement = count_statement.where(InventoryMovement.movement_type == movement_type)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [
            serialize_movement(item)
            for item in items
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


def create_manual_movement(db: Session, data: InventoryMovementCreateRequest, user: User) -> InventoryMovement:
    return apply_movement(db, data.inventory_id, data.movement_type, data.quantity, data.reason, user)


def serialize_movement(movement: InventoryMovement) -> dict[str, object]:
    return {
        "id": movement.id,
        "inventory_id": movement.inventory_id,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "stock_before": movement.stock_before,
        "stock_after": movement.stock_after,
        "reason": movement.reason,
        "reference_type": movement.reference_type,
        "reference_id": movement.reference_id,
        "created_by": movement.created_by,
        "created_at": movement.created_at,
    }


def reserve_stock(db: Session, inventory_id: int, quantity: int, reference_id: int) -> Inventory:
    item = get_locked_inventory(db, inventory_id)
    available = item.stock_quantity - item.reserved_quantity
    if available < quantity:
        raise _error("INSUFFICIENT_STOCK", "No existe disponibilidad suficiente para reservar.", status.HTTP_409_CONFLICT)
    item.reserved_quantity += quantity
    db.add(InventoryMovement(
        inventory_id=item.id,
        movement_type="RESERVE",
        quantity=quantity,
        stock_before=item.stock_quantity,
        stock_after=item.stock_quantity,
        reason="Reserva de prendas",
        reference_type="reservation",
        reference_id=reference_id,
    ))
    db.flush()
    return item


def release_stock(db: Session, inventory_id: int, quantity: int, reference_id: int) -> Inventory:
    item = get_locked_inventory(db, inventory_id)
    if item.reserved_quantity < quantity:
        raise _error("INVALID_RESERVED_STOCK", "La liberación supera las unidades reservadas.", status.HTTP_409_CONFLICT)
    item.reserved_quantity -= quantity
    db.add(InventoryMovement(
        inventory_id=item.id,
        movement_type="RELEASE",
        quantity=quantity,
        stock_before=item.stock_quantity,
        stock_after=item.stock_quantity,
        reason="Liberación de reserva",
        reference_type="reservation",
        reference_id=reference_id,
    ))
    db.flush()
    return item

from datetime import UTC, datetime
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.audit import record_audit
from app.core.models import Branch, Inventory, InventoryMovement, InventoryQuarantine, ProductVariant, User
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
    # Lock only the inventory row. PostgreSQL rejects FOR UPDATE on nullable
    # sides of the outer joins used by the serialization query.
    item = db.scalar(select(Inventory).where(Inventory.id == inventory_id).with_for_update())
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
    if movement_type not in {"IN", "OUT", "RETURN", "RESERVE", "RELEASE", "SALE"}:
        raise _error("INVALID_MOVEMENT_TYPE", "El tipo de movimiento no es válido.", status.HTTP_400_BAD_REQUEST)
    if quantity <= 0:
        raise _error("INVALID_MOVEMENT_QUANTITY", "La cantidad debe ser mayor que cero.", status.HTTP_400_BAD_REQUEST)
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
    record_audit(
        db,
        user,
        "CREATE",
        "inventory_movement",
        movement.id,
        "Movimiento de inventario registrado.",
        new_values={"inventory_id": movement.inventory_id, "movement_type": movement.movement_type, "quantity": movement.quantity, "stock_before": movement.stock_before, "stock_after": movement.stock_after, "reference_type": movement.reference_type, "reference_id": movement.reference_id},
    )
    return movement


def create_manual_movement(db: Session, data: InventoryMovementCreateRequest, user: User) -> InventoryMovement:
    reason = data.reason.strip()
    if len(reason) < 2:
        raise _error("INVALID_REASON", "El motivo debe contener al menos dos caracteres.", status.HTTP_400_BAD_REQUEST)
    return apply_movement(db, data.inventory_id, data.movement_type, data.quantity, reason, user)


def list_movements(
    db: Session,
    page: int,
    page_size: int,
    inventory_id: int | None,
    movement_type: str | None,
    allowed_branch_ids: set[int] | None = None,
) -> dict[str, object]:
    statement = select(InventoryMovement).options(joinedload(InventoryMovement.inventory).joinedload(Inventory.branch)).join(Inventory, InventoryMovement.inventory_id == Inventory.id).order_by(InventoryMovement.id.desc())
    count_statement = select(func.count(InventoryMovement.id)).join(Inventory, InventoryMovement.inventory_id == Inventory.id)
    if inventory_id is not None:
        statement = statement.where(InventoryMovement.inventory_id == inventory_id)
        count_statement = count_statement.where(InventoryMovement.inventory_id == inventory_id)
    if movement_type is not None:
        statement = statement.where(InventoryMovement.movement_type == movement_type)
        count_statement = count_statement.where(InventoryMovement.movement_type == movement_type)
    if allowed_branch_ids is not None:
        statement = statement.where(Inventory.branch_id.in_(allowed_branch_ids))
        count_statement = count_statement.where(Inventory.branch_id.in_(allowed_branch_ids))
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [serialize_movement(item) for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


def serialize_quarantine(item: InventoryQuarantine) -> dict[str, object]:
    return {
        "id": item.id,
        "tenant_id": item.tenant_id,
        "branch_id": item.branch_id,
        "inventory_id": item.inventory_id,
        "product_variant_id": item.product_variant_id,
        "exchange_item_id": item.exchange_item_id,
        "quantity": item.quantity,
        "status": item.status,
        "inspected_by": item.inspected_by,
        "inspection_reason": item.inspection_reason,
        "inspected_at": item.inspected_at,
        "created_at": item.created_at,
    }


def list_quarantine(db: Session, page: int, page_size: int, status_filter: str | None, tenant_id: int, allowed_branch_ids: set[int] | None = None) -> dict[str, object]:
    statement = select(InventoryQuarantine).where(InventoryQuarantine.tenant_id == tenant_id).order_by(InventoryQuarantine.id.desc())
    count_statement = select(func.count(InventoryQuarantine.id)).where(InventoryQuarantine.tenant_id == tenant_id)
    if status_filter is not None:
        statement = statement.where(InventoryQuarantine.status == status_filter)
        count_statement = count_statement.where(InventoryQuarantine.status == status_filter)
    if allowed_branch_ids is not None:
        statement = statement.where(InventoryQuarantine.branch_id.in_(allowed_branch_ids))
        count_statement = count_statement.where(InventoryQuarantine.branch_id.in_(allowed_branch_ids))
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_quarantine(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_locked_quarantine(db: Session, quarantine_id: int, tenant_id: int) -> InventoryQuarantine:
    item = db.scalar(select(InventoryQuarantine).where(InventoryQuarantine.id == quarantine_id, InventoryQuarantine.tenant_id == tenant_id).with_for_update())
    if item is None:
        raise _error("QUARANTINE_NOT_FOUND", "Registro de cuarentena no encontrado.", status.HTTP_404_NOT_FOUND)
    return item


def inspect_quarantine(db: Session, quarantine: InventoryQuarantine, inventory: Inventory, decision: str, reason: str, user: User) -> InventoryQuarantine:
    if decision not in {"RELEASE", "REJECT"}:
        raise _error("INVALID_INSPECTION_DECISION", "La decisión debe ser RELEASE o REJECT.", status.HTTP_400_BAD_REQUEST)
    clean_reason = reason.strip()
    if len(clean_reason) < 2:
        raise _error("INVALID_REASON", "El motivo debe contener al menos dos caracteres.", status.HTTP_400_BAD_REQUEST)
    if quarantine.status != "PENDING":
        if quarantine.status == ("RELEASED" if decision == "RELEASE" else "REJECTED"):
            return quarantine
        raise _error("QUARANTINE_ALREADY_INSPECTED", "La cuarentena ya fue resuelta con una decisión distinta.", status.HTTP_409_CONFLICT)
    old_status = quarantine.status
    now = datetime.now(UTC)
    quarantine.status = "RELEASED" if decision == "RELEASE" else "REJECTED"
    quarantine.inspected_by = user.id
    quarantine.inspection_reason = clean_reason
    quarantine.inspected_at = now
    if decision == "RELEASE":
        before = inventory.stock_quantity
        inventory.stock_quantity += quarantine.quantity
        movement = InventoryMovement(tenant_id=user.tenant_id, inventory_id=inventory.id, movement_type="IN", quantity=quarantine.quantity, stock_before=before, stock_after=inventory.stock_quantity, reason=clean_reason, reference_type="inventory_quarantine", reference_id=quarantine.id, created_by=user.id)
        db.add(movement)
        db.flush()
        record_audit(db, user, "CREATE", "inventory_movement", movement.id, "Prendas liberadas de cuarentena.", new_values={"quarantine_id": quarantine.id, "quantity": quarantine.quantity, "movement_type": "IN"})
    record_audit(db, user, "UPDATE", "inventory_quarantine", quarantine.id, "Inspección de prenda en cuarentena.", old_values={"status": old_status}, new_values={"status": quarantine.status, "decision": decision, "reason": clean_reason})
    db.flush()
    return quarantine


def serialize_movement(movement: InventoryMovement) -> dict[str, object]:
    return {
        "id": movement.id,
        "inventory_id": movement.inventory_id,
        "branch_id": movement.inventory.branch_id,
        "branch_name": movement.inventory.branch.name,
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


def reserve_stock(db: Session, inventory_id: int, quantity: int, reference_id: int, user: User | None = None) -> Inventory:
    item = get_locked_inventory(db, inventory_id)
    available = item.stock_quantity - item.reserved_quantity
    if available < quantity:
        raise _error("INSUFFICIENT_STOCK", "No existe disponibilidad suficiente para reservar.", status.HTTP_409_CONFLICT)
    item.reserved_quantity += quantity
    movement = InventoryMovement(
        inventory_id=item.id,
        movement_type="RESERVE",
        quantity=quantity,
        stock_before=item.stock_quantity,
        stock_after=item.stock_quantity,
        reason="Reserva de prendas",
        reference_type="reservation",
        reference_id=reference_id,
        created_by=user.id if user else None,
    )
    db.add(movement)
    db.flush()
    record_audit(db, user, "CREATE", "inventory_movement", movement.id, "Reserva de inventario registrada.", new_values={"inventory_id": item.id, "movement_type": "RESERVE", "quantity": quantity, "reserved_after": item.reserved_quantity, "reference_type": "reservation", "reference_id": reference_id})
    return item


def release_stock(db: Session, inventory_id: int, quantity: int, reference_id: int, user: User | None = None, reason: str = "Liberación de reserva") -> Inventory:
    item = get_locked_inventory(db, inventory_id)
    if item.reserved_quantity < quantity:
        raise _error("INVALID_RESERVED_STOCK", "La liberación supera las unidades reservadas.", status.HTTP_409_CONFLICT)
    item.reserved_quantity -= quantity
    movement = InventoryMovement(
        inventory_id=item.id,
        movement_type="RELEASE",
        quantity=quantity,
        stock_before=item.stock_quantity,
        stock_after=item.stock_quantity,
        reason=reason,
        reference_type="reservation",
        reference_id=reference_id,
        created_by=user.id if user else None,
    )
    db.add(movement)
    db.flush()
    record_audit(db, user, "CREATE", "inventory_movement", movement.id, "Liberación de inventario registrada.", new_values={"inventory_id": item.id, "movement_type": "RELEASE", "quantity": quantity, "reserved_after": item.reserved_quantity, "reference_type": "reservation", "reference_id": reference_id})
    return item

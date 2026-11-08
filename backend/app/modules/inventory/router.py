from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.core.audit import record_audit
from app.core.models import User
from app.modules.auth.dependencies import require_branch_access, require_permission
from app.modules.inventory import service
from app.modules.inventory.schemas import InventoryCreateRequest, InventoryMovementCreateRequest, InventoryMovementPage, InventoryMovementResponse, InventoryPage, InventoryResponse, InventoryUpdateRequest, QuarantineInspectionRequest, QuarantinePage, QuarantineResponse

router = APIRouter(prefix="/inventory", tags=["inventory"])
InventoryReader = Annotated[User, Depends(require_permission("inventory.read"))]
InventoryWriter = Annotated[User, Depends(require_permission("inventory.adjust"))]


def require_quarantine_inspector(current_user: InventoryWriter) -> User:
    if current_user.role.code not in {"ADMIN", "BRANCH_MANAGER"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "QUARANTINE_INSPECTION_FORBIDDEN", "message": "Solo ADMIN o BRANCH_MANAGER pueden inspeccionar cuarentena."})
    return current_user


@router.get("", response_model=InventoryPage)
def list_inventory(current_user: InventoryReader, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), branch_id: int | None = Query(None, gt=0), product_id: int | None = Query(None, gt=0)):
    if branch_id is not None:
        require_branch_access(current_user, branch_id)
    allowed = None if current_user.role.code == "ADMIN" else {branch.id for branch in current_user.branches}
    return service.list_inventory(db, page, page_size, branch_id, product_id, allowed)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(data: InventoryCreateRequest, current_user: InventoryWriter, db=Depends(get_db)):
    require_branch_access(current_user, data.branch_id)
    try:
        item = service.create_inventory(db, data)
        record_audit(db, current_user, "CREATE", "inventory", item.id, "Inventario creado.", new_values={"branch_id": item.branch_id, "product_variant_id": item.product_variant_id, "stock_quantity": item.stock_quantity})
        db.commit()
    except Exception:
        db.rollback()
        raise
    return service.serialize_inventory(item)


@router.get("/quarantine", response_model=QuarantinePage)
def list_quarantine(current_user: InventoryReader, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status_filter: str | None = Query(None, alias="status", pattern="^(PENDING|RELEASED|REJECTED)$")):
    allowed = None if current_user.role.code == "ADMIN" else {branch.id for branch in current_user.branches}
    return service.list_quarantine(db, page, page_size, status_filter, current_user.tenant_id, allowed)


@router.post("/quarantine/{quarantine_id}/inspection", response_model=QuarantineResponse)
def inspect_quarantine(quarantine_id: int, data: QuarantineInspectionRequest, current_user: User = Depends(require_quarantine_inspector), db=Depends(get_db)):
    quarantine = service.get_locked_quarantine(db, quarantine_id, current_user.tenant_id)
    require_branch_access(current_user, quarantine.branch_id)
    inventory = service.get_locked_inventory(db, quarantine.inventory_id)
    if inventory.tenant_id != current_user.tenant_id or inventory.branch_id != quarantine.branch_id or inventory.product_variant_id != quarantine.product_variant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "QUARANTINE_NOT_FOUND", "message": "Registro de cuarentena no encontrado."})
    try:
        result = service.inspect_quarantine(db, quarantine, inventory, data.decision, data.reason, current_user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return service.serialize_quarantine(result)


@router.get("/movements", response_model=InventoryMovementPage)
def list_movements(current_user: InventoryReader, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), inventory_id: int | None = Query(None, gt=0), movement_type: str | None = Query(None, pattern="^(IN|OUT|RETURN|RESTOCK|RESERVE|RELEASE|SALE)$")):
    if inventory_id is not None:
        item = service.get_inventory(db, inventory_id)
        require_branch_access(current_user, item.branch_id)
    allowed = None if current_user.role.code == "ADMIN" else {branch.id for branch in current_user.branches}
    return service.list_movements(db, page, page_size, inventory_id, movement_type, allowed)


@router.post("/movements", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(data: InventoryMovementCreateRequest, current_user: InventoryWriter, db=Depends(get_db)):
    item = service.get_inventory(db, data.inventory_id)
    require_branch_access(current_user, item.branch_id)
    try:
        movement = service.create_manual_movement(db, data, current_user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return service.serialize_movement(movement)


@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory(inventory_id: int, current_user: InventoryReader, db=Depends(get_db)):
    item = service.get_inventory(db, inventory_id)
    require_branch_access(current_user, item.branch_id)
    return service.serialize_inventory(item)


@router.patch("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(inventory_id: int, data: InventoryUpdateRequest, current_user: InventoryWriter, db=Depends(get_db)):
    item = service.get_locked_inventory(db, inventory_id)
    require_branch_access(current_user, item.branch_id)
    try:
        old_stock = item.stock_quantity
        item = service.update_inventory(db, item, data, current_user)
        record_audit(db, current_user, "UPDATE", "inventory", item.id, "Stock de inventario actualizado.", old_values={"stock_quantity": old_stock}, new_values={"stock_quantity": item.stock_quantity, "reserved_quantity": item.reserved_quantity, "available_quantity": item.stock_quantity - item.reserved_quantity})
        db.commit()
    except Exception:
        db.rollback()
        raise
    return service.serialize_inventory(item)

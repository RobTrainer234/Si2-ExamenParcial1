from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.audit import record_audit
from app.core.models import User
from app.modules.auth.dependencies import require_branch_access, require_permission
from app.modules.inventory import service
from app.modules.inventory.schemas import InventoryCreateRequest, InventoryPage, InventoryResponse, InventoryUpdateRequest

router = APIRouter(prefix="/inventory", tags=["inventory"])
InventoryReader = Annotated[User, Depends(require_permission("inventory.read"))]
InventoryWriter = Annotated[User, Depends(require_permission("inventory.adjust"))]


@router.get("", response_model=InventoryPage)
def list_inventory(current_user: InventoryReader, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), branch_id: int | None = Query(None, gt=0), product_id: int | None = Query(None, gt=0)):
    if branch_id is not None:
        require_branch_access(current_user, branch_id)
    allowed = None if current_user.role.code == "ADMIN" else {branch.id for branch in current_user.branches}
    return service.list_inventory(db, page, page_size, branch_id, product_id, allowed)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(data: InventoryCreateRequest, current_user: InventoryWriter, db=Depends(get_db)):
    require_branch_access(current_user, data.branch_id)
    item = service.create_inventory(db, data)
    record_audit(db, current_user, "CREATE", "inventory", item.id, "Inventario creado.", new_values={"branch_id": item.branch_id, "product_variant_id": item.product_variant_id, "stock_quantity": item.stock_quantity})
    db.commit()
    return service.serialize_inventory(item)


@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory(inventory_id: int, current_user: InventoryReader, db=Depends(get_db)):
    item = service.get_inventory(db, inventory_id)
    require_branch_access(current_user, item.branch_id)
    return service.serialize_inventory(item)


@router.patch("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(inventory_id: int, data: InventoryUpdateRequest, current_user: InventoryWriter, db=Depends(get_db)):
    item = service.get_inventory(db, inventory_id)
    require_branch_access(current_user, item.branch_id)
    old_stock = item.stock_quantity
    item = service.update_inventory(db, item, data, current_user)
    record_audit(db, current_user, "UPDATE", "inventory", item.id, "Stock de inventario actualizado.", old_values={"stock_quantity": old_stock}, new_values={"stock_quantity": item.stock_quantity})
    db.commit()
    return service.serialize_inventory(item)

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_admin
from app.modules.inventory import service
from app.modules.inventory.schemas import InventoryCreateRequest, InventoryPage, InventoryResponse, InventoryUpdateRequest

router = APIRouter(prefix="/inventory", tags=["inventory"])
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=InventoryPage)
def list_inventory(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), branch_id: int | None = Query(None, gt=0), product_id: int | None = Query(None, gt=0)):
    return service.list_inventory(db, page, page_size, branch_id, product_id)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(data: InventoryCreateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.create_inventory(db, data)
    db.commit()
    return service.serialize_inventory(item)


@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory(inventory_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_inventory(service.get_inventory(db, inventory_id))


@router.patch("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(inventory_id: int, data: InventoryUpdateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.update_inventory(db, service.get_inventory(db, inventory_id), data)
    db.commit()
    return service.serialize_inventory(item)

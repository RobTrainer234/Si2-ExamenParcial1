from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_admin
from app.modules.suppliers import service
from app.modules.suppliers.schemas import SupplierCreateRequest, SupplierPage, SupplierResponse, SupplierUpdateRequest

router = APIRouter(prefix="/suppliers", tags=["suppliers"])
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=SupplierPage)
def list_suppliers(
    _: AdminUser,
    db=Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
):
    return service.list_suppliers(db, page, page_size, q)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(data: SupplierCreateRequest, _: AdminUser, db=Depends(get_db)):
    supplier = service.create_supplier(db, data)
    db.commit()
    return service.serialize_supplier(supplier)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_supplier(service.get_supplier(db, supplier_id))


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, data: SupplierUpdateRequest, _: AdminUser, db=Depends(get_db)):
    supplier = service.update_supplier(db, service.get_supplier(db, supplier_id), data)
    db.commit()
    return service.serialize_supplier(supplier)


@router.patch("/{supplier_id}/activate", response_model=SupplierResponse)
def activate_supplier(supplier_id: int, _: AdminUser, db=Depends(get_db)):
    supplier = service.set_active(db, service.get_supplier(db, supplier_id), True)
    db.commit()
    return service.serialize_supplier(supplier)


@router.patch("/{supplier_id}/deactivate", response_model=SupplierResponse)
def deactivate_supplier(supplier_id: int, _: AdminUser, db=Depends(get_db)):
    supplier = service.set_active(db, service.get_supplier(db, supplier_id), False)
    db.commit()
    return service.serialize_supplier(supplier)

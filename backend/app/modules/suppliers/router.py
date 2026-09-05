from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.suppliers import service
from app.modules.suppliers.schemas import SupplyOfferAdminUpdateRequest, SupplyOfferCreateRequest, SupplyOfferResponse, SupplyOfferSupplierUpdateRequest, SupplierCreateRequest, SupplierPage, SupplierPortalResponse, SupplierResponse, SupplierUpdateRequest

router = APIRouter(prefix="/suppliers", tags=["suppliers"])
AdminUser = Annotated[User, Depends(require_permission("suppliers.manage"))]
SupplierUser = Annotated[User, Depends(require_permission("suppliers.portal"))]


@router.get("/me", response_model=SupplierPortalResponse)
def supplier_portal(current_user: SupplierUser, db=Depends(get_db)):
    return service.supplier_portal(db, current_user)


@router.get("/me/offers", response_model=list[SupplyOfferResponse])
def my_supply_offers(current_user: SupplierUser, db=Depends(get_db)):
    if current_user.supplier_id is None:
        return []
    return service.list_offers(db, supplier_id=current_user.supplier_id, active_only=True)


@router.patch("/me/offers/{offer_id}", response_model=SupplyOfferResponse)
def update_my_supply_offer(offer_id: int, data: SupplyOfferSupplierUpdateRequest, current_user: SupplierUser, db=Depends(get_db)):
    offer = service.get_offer(db, offer_id, current_user.supplier_id)
    old_values = {field: getattr(offer, field) for field in data.model_dump(exclude_unset=True)}
    offer = service.update_supplier_offer(db, offer, data)
    record_audit(db, current_user, "UPDATE", "supply_offer", offer.id, "Disponibilidad de abastecimiento actualizada por proveedor.", old_values=old_values, new_values=data.model_dump(exclude_unset=True))
    db.commit()
    return service.serialize_offer(offer)


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
def create_supplier(data: SupplierCreateRequest, current_user: AdminUser, db=Depends(get_db)):
    supplier = service.create_supplier(db, data)
    record_audit(db, current_user, "CREATE", "supplier", supplier.id, "Proveedor creado.", new_values={"trade_name": supplier.trade_name, "tax_id": supplier.tax_id})
    db.commit()
    return service.serialize_supplier(supplier)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_supplier(service.get_supplier(db, supplier_id))


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, data: SupplierUpdateRequest, current_user: AdminUser, db=Depends(get_db)):
    supplier = service.get_supplier(db, supplier_id)
    old_values = {field: getattr(supplier, field) for field in data.model_dump(exclude_unset=True)}
    supplier = service.update_supplier(db, supplier, data)
    record_audit(db, current_user, "UPDATE", "supplier", supplier.id, "Proveedor actualizado.", old_values=old_values, new_values=data.model_dump(exclude_unset=True))
    db.commit()
    return service.serialize_supplier(supplier)


@router.patch("/{supplier_id}/activate", response_model=SupplierResponse)
def activate_supplier(supplier_id: int, current_user: AdminUser, db=Depends(get_db)):
    supplier = service.set_active(db, service.get_supplier(db, supplier_id), True)
    record_audit(db, current_user, "UPDATE", "supplier", supplier.id, "Proveedor activado.", new_values={"is_active": True})
    db.commit()
    return service.serialize_supplier(supplier)


@router.patch("/{supplier_id}/deactivate", response_model=SupplierResponse)
def deactivate_supplier(supplier_id: int, current_user: AdminUser, db=Depends(get_db)):
    supplier = service.set_active(db, service.get_supplier(db, supplier_id), False)
    record_audit(db, current_user, "UPDATE", "supplier", supplier.id, "Proveedor desactivado.", new_values={"is_active": False})
    db.commit()
    return service.serialize_supplier(supplier)


@router.get("/{supplier_id}/offers", response_model=list[SupplyOfferResponse])
def list_supplier_offers(
    supplier_id: int,
    _: AdminUser,
    db=Depends(get_db),
    product_id: int | None = Query(default=None, gt=0),
    season_id: int | None = Query(default=None, gt=0),
    collection_id: int | None = Query(default=None, gt=0),
):
    service.get_supplier(db, supplier_id)
    return service.list_offers(db, supplier_id, product_id, season_id, collection_id)


@router.post("/{supplier_id}/offers", response_model=SupplyOfferResponse, status_code=status.HTTP_201_CREATED)
def create_supplier_offer(supplier_id: int, data: SupplyOfferCreateRequest, current_user: AdminUser, db=Depends(get_db)):
    offer = service.create_offer(db, supplier_id, data)
    record_audit(db, current_user, "CREATE", "supply_offer", offer.id, "Oferta de abastecimiento creada.", new_values=data.model_dump())
    db.commit()
    return service.serialize_offer(offer)


@router.patch("/{supplier_id}/offers/{offer_id}", response_model=SupplyOfferResponse)
def update_supplier_offer(supplier_id: int, offer_id: int, data: SupplyOfferAdminUpdateRequest, current_user: AdminUser, db=Depends(get_db)):
    offer = service.get_offer(db, offer_id, supplier_id)
    old_values = {field: getattr(offer, field) for field in data.model_dump(exclude_unset=True)}
    offer = service.update_offer(db, offer, data)
    record_audit(db, current_user, "UPDATE", "supply_offer", offer.id, "Oferta de abastecimiento actualizada.", old_values=old_values, new_values=data.model_dump(exclude_unset=True))
    db.commit()
    return service.serialize_offer(offer)


@router.patch("/{supplier_id}/offers/{offer_id}/{action}", response_model=SupplyOfferResponse)
def set_supplier_offer_status(supplier_id: int, offer_id: int, action: str, current_user: AdminUser, db=Depends(get_db)):
    if action not in {"activate", "deactivate"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    offer = service.get_offer(db, offer_id, supplier_id)
    offer.is_active = action == "activate"
    record_audit(db, current_user, "UPDATE", "supply_offer", offer.id, f"Oferta de abastecimiento {'activada' if offer.is_active else 'desactivada'}.", new_values={"is_active": offer.is_active})
    db.commit()
    return service.serialize_offer(offer)

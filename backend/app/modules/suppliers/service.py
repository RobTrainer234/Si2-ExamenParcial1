from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import Supplier
from app.modules.suppliers.schemas import SupplierCreateRequest, SupplierUpdateRequest


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "SUPPLIER_CONFLICT", "message": message})


def serialize_supplier(supplier: Supplier) -> dict[str, object]:
    return {
        "id": supplier.id,
        "trade_name": supplier.trade_name,
        "legal_name": supplier.legal_name,
        "tax_id": supplier.tax_id,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
        "is_active": supplier.is_active,
    }


def list_suppliers(db: Session, page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(Supplier).order_by(Supplier.trade_name)
    count_statement = select(func.count(Supplier.id))
    if query:
        search = f"%{query.strip()}%"
        condition = or_(Supplier.trade_name.ilike(search), Supplier.legal_name.ilike(search), Supplier.tax_id.ilike(search))
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_supplier(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_supplier(db: Session, supplier_id: int) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "SUPPLIER_NOT_FOUND", "message": "Proveedor no encontrado."})
    return supplier


def create_supplier(db: Session, data: SupplierCreateRequest) -> Supplier:
    values = data.model_dump()
    if values["tax_id"] and db.scalar(select(Supplier.id).where(Supplier.tax_id == values["tax_id"])):
        raise _conflict("La identificación fiscal ya está registrada.")
    supplier = Supplier(**values)
    db.add(supplier)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("La identificación fiscal ya está registrada.") from exc
    return supplier


def update_supplier(db: Session, supplier: Supplier, data: SupplierUpdateRequest) -> Supplier:
    values = data.model_dump(exclude_unset=True)
    if values.get("tax_id"):
        existing = db.scalar(select(Supplier.id).where(Supplier.tax_id == values["tax_id"], Supplier.id != supplier.id))
        if existing:
            raise _conflict("La identificación fiscal ya está registrada.")
    for field, value in values.items():
        setattr(supplier, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("La identificación fiscal ya está registrada.") from exc
    return supplier


def set_active(db: Session, supplier: Supplier, active: bool) -> Supplier:
    supplier.is_active = active
    db.flush()
    return supplier

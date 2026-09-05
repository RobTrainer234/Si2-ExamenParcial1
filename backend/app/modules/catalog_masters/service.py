from math import ceil
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import Category, Color, Product, ProductVariant, Size


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "MASTER_CONFLICT", "message": message})


def serialize_master(item: Any) -> dict[str, object]:
    data = {"id": item.id, "name": item.name, "is_active": item.is_active}
    if isinstance(item, Category):
        data["description"] = item.description
    if isinstance(item, Color):
        data["hex_code"] = item.hex_code
    if isinstance(item, Size):
        data["size_type"] = item.size_type
        data["sort_order"] = item.sort_order
    return data


def list_master(db: Session, model: type[Any], page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(model).order_by(model.sort_order, model.name) if model is Size else select(model).order_by(model.name)
    count_statement = select(func.count(model.id))
    if query:
        condition = model.name.ilike(f"%{query.strip()}%")
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_master(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_master(db: Session, model: type[Any], item_id: int, code: str, label: str) -> Any:
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": code, "message": f"{label} no encontrado."})
    return item


def create_master(db: Session, model: type[Any], values: dict[str, object], label: str) -> Any:
    name = str(values["name"]).strip()
    if db.scalar(select(model.id).where(model.name == name)):
        raise _conflict(f"El {label.lower()} ya está registrado.")
    values["name"] = name
    if model is Size:
        if name.isdigit() and values.get("size_type") == "ALPHA":
            values["size_type"] = "NUMERIC"
        if name.lower() in {"unica", "única", "one size", "os"}:
            values["size_type"] = "ONE_SIZE"
        if not values.get("sort_order"):
            values["sort_order"] = int(name) if name.isdigit() else {"XS": 10, "S": 20, "M": 30, "L": 40, "XL": 50, "XXL": 60}.get(name.upper(), 100)
    item = model(**values)
    db.add(item)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(f"El {label.lower()} ya está registrado.") from exc
    return item


def update_master(db: Session, item: Any, values: dict[str, object], label: str) -> Any:
    if "name" in values and values["name"] is not None:
        name = str(values["name"]).strip()
        if db.scalar(select(item.__class__.id).where(item.__class__.name == name, item.__class__.id != item.id)):
            raise _conflict(f"El {label.lower()} ya está registrado.")
        values["name"] = name
    for field, value in values.items():
        setattr(item, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(f"El {label.lower()} ya está registrado.") from exc
    return item


def set_active(db: Session, item: Any, active: bool) -> Any:
    if not active:
        if isinstance(item, Category) and db.scalar(select(Product.id).where(Product.category_id == item.id, Product.is_active.is_(True))):
            raise _conflict("No se puede desactivar una categoría asociada a productos activos.")
        if isinstance(item, Size) and db.scalar(select(ProductVariant.id).where(ProductVariant.size_id == item.id, ProductVariant.is_active.is_(True))):
            raise _conflict("No se puede desactivar una talla asociada a variantes activas.")
        if isinstance(item, Color) and db.scalar(select(ProductVariant.id).where(ProductVariant.color_id == item.id, ProductVariant.is_active.is_(True))):
            raise _conflict("No se puede desactivar un color asociado a variantes activas.")
    item.is_active = active
    db.flush()
    return item

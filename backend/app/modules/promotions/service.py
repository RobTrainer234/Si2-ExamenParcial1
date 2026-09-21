from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.models import Product, Promotion, PromotionProduct, User
from app.modules.promotions.schemas import PromotionCreate, PromotionUpdate


def error(code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _promotion_query():
    return select(Promotion).options(selectinload(Promotion.products))


def serialize(item: Promotion) -> dict[str, object]:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "discount_type": item.discount_type,
        "discount_value": item.discount_value,
        "starts_at": item.starts_at,
        "ends_at": item.ends_at,
        "is_active": item.is_active,
        "product_ids": [product.product_id for product in item.products],
    }


def list_promotions(db: Session, page: int, page_size: int, q: str | None = None) -> dict[str, object]:
    statement = _promotion_query().order_by(Promotion.starts_at.desc(), Promotion.name)
    count_statement = select(func.count(Promotion.id))
    if q:
        search = f"%{q.strip()}%"
        statement = statement.where(Promotion.name.ilike(search))
        count_statement = count_statement.where(Promotion.name.ilike(search))
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_promotion(db: Session, promotion_id: int) -> Promotion:
    item = db.scalar(_promotion_query().where(Promotion.id == promotion_id))
    if item is None:
        raise error("PROMOTION_NOT_FOUND", "Promoción no encontrada.", status.HTTP_404_NOT_FOUND)
    return item


def _validate_update_dates(item: Promotion) -> None:
    if item.ends_at <= item.starts_at:
        raise error("INVALID_PROMOTION_DATES", "La fecha final debe ser posterior a la fecha inicial.")
    if item.discount_type == "PERCENT" and item.discount_value > 100:
        raise error("INVALID_PROMOTION_PERCENT", "El porcentaje no puede superar 100.")


def create_promotion(db: Session, data: PromotionCreate, user: User) -> Promotion:
    item = Promotion(**data.model_dump())
    db.add(item)
    db.flush()
    record_audit(db, user, "CREATE", "promotion", item.id, "Promoción creada.", new_values=serialize(get_promotion(db, item.id)))
    return get_promotion(db, item.id)


def update_promotion(db: Session, promotion_id: int, data: PromotionUpdate, user: User) -> Promotion:
    item = get_promotion(db, promotion_id)
    old = serialize(item)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    _validate_update_dates(item)
    db.flush()
    updated = get_promotion(db, promotion_id)
    record_audit(db, user, "UPDATE", "promotion", item.id, "Promoción actualizada.", old_values=old, new_values=serialize(updated))
    return updated


def set_status(db: Session, promotion_id: int, active: bool, user: User) -> Promotion:
    item = get_promotion(db, promotion_id)
    old = serialize(item)
    item.is_active = active
    db.flush()
    updated = get_promotion(db, promotion_id)
    record_audit(db, user, "UPDATE", "promotion", item.id, "Estado de promoción actualizado.", old_values=old, new_values=serialize(updated))
    return updated


def set_products(db: Session, promotion_id: int, product_ids: list[int], user: User) -> Promotion:
    item = get_promotion(db, promotion_id)
    unique_ids = sorted(set(product_ids))
    found = set(db.scalars(select(Product.id).where(Product.id.in_(unique_ids), Product.is_active.is_(True))).all())
    missing = [product_id for product_id in unique_ids if product_id not in found]
    if missing:
        raise error("PROMOTION_PRODUCT_NOT_FOUND", "Uno o más productos no existen o están inactivos.", status.HTTP_404_NOT_FOUND)
    old = serialize(item)
    item.products.clear()
    db.flush()
    item.products.extend(PromotionProduct(product_id=product_id) for product_id in unique_ids)
    db.flush()
    updated = get_promotion(db, promotion_id)
    record_audit(db, user, "UPDATE", "promotion", item.id, "Productos de promoción actualizados.", old_values=old, new_values=serialize(updated))
    return updated

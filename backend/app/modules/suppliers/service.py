from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.models import Collection, Product, ProductSupplier, ProductVariant, Season, Supplier, SupplierSupplyOffer, User
from app.modules.suppliers.schemas import SupplyOfferAdminUpdateRequest, SupplyOfferCreateRequest, SupplyOfferSupplierUpdateRequest, SupplierCreateRequest, SupplierUpdateRequest


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
        "product_ids": [link.product_id for link in supplier.products],
    }


def list_suppliers(db: Session, page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(Supplier).options(selectinload(Supplier.products)).order_by(Supplier.trade_name)
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
    supplier = db.scalar(select(Supplier).options(selectinload(Supplier.products)).where(Supplier.id == supplier_id))
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


def supplier_portal(db: Session, user: User) -> dict[str, object]:
    if user.supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "SUPPLIER_ACCOUNT_NOT_LINKED", "message": "La cuenta no está asociada a un proveedor."})
    products = db.scalars(select(Product).where(Product.suppliers.any(supplier_id=user.supplier.id)).order_by(Product.name)).all()
    return {
        "supplier_id": user.supplier.id,
        "trade_name": user.supplier.trade_name,
        "products": [{"id": product.id, "code": product.code, "name": product.name, "is_active": product.is_active} for product in products],
    }


def _offer_query():
    return select(SupplierSupplyOffer).options(
        joinedload(SupplierSupplyOffer.supplier),
        joinedload(SupplierSupplyOffer.product_variant).joinedload(ProductVariant.product),
        joinedload(SupplierSupplyOffer.product_variant).joinedload(ProductVariant.size),
        joinedload(SupplierSupplyOffer.product_variant).joinedload(ProductVariant.color),
        joinedload(SupplierSupplyOffer.season),
        joinedload(SupplierSupplyOffer.collection),
    )


def serialize_offer(offer: SupplierSupplyOffer) -> dict[str, object]:
    variant = offer.product_variant
    return {
        "id": offer.id,
        "supplier_id": offer.supplier_id,
        "supplier_name": offer.supplier.trade_name,
        "product_id": variant.product_id,
        "product_name": variant.product.name,
        "product_variant_id": offer.product_variant_id,
        "sku": variant.sku,
        "size_name": variant.size.name,
        "color_name": variant.color.name,
        "season_id": offer.season_id,
        "season_name": offer.season.name,
        "collection_id": offer.collection_id,
        "collection_name": offer.collection.name if offer.collection else None,
        "status": offer.status,
        "available_quantity": offer.available_quantity,
        "expected_date": offer.expected_date,
        "notes": offer.notes,
        "is_active": offer.is_active,
    }


def get_offer(db: Session, offer_id: int, supplier_id: int | None = None) -> SupplierSupplyOffer:
    statement = _offer_query().where(SupplierSupplyOffer.id == offer_id)
    if supplier_id is not None:
        statement = statement.where(SupplierSupplyOffer.supplier_id == supplier_id)
    offer = db.scalar(statement)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "SUPPLY_OFFER_NOT_FOUND", "message": "Oferta de abastecimiento no encontrada."})
    return offer


def _validate_offer_references(db: Session, supplier_id: int, variant_id: int, season_id: int, collection_id: int | None) -> None:
    supplier = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.is_active.is_(True)))
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SUPPLIER_NOT_FOUND_OR_INACTIVE", "message": "El proveedor no existe o está inactivo."})
    variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == variant_id, ProductVariant.is_active.is_(True)))
    if variant is None or not variant.product.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VARIANT_NOT_FOUND_OR_INACTIVE", "message": "La variante no existe o está inactiva."})
    if db.scalar(select(ProductSupplier.product_id).where(ProductSupplier.product_id == variant.product_id, ProductSupplier.supplier_id == supplier_id)) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SUPPLIER_PRODUCT_NOT_LINKED", "message": "El proveedor no está asociado al producto de la variante."})
    season = db.scalar(select(Season).where(Season.id == season_id, Season.is_active.is_(True)))
    if season is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SEASON_NOT_FOUND_OR_INACTIVE", "message": "La temporada no existe o está inactiva."})
    if collection_id is not None:
        collection = db.scalar(select(Collection).where(Collection.id == collection_id, Collection.is_active.is_(True)))
        if collection is None or collection.season_id != season_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "COLLECTION_SEASON_MISMATCH", "message": "La colección no pertenece a la temporada seleccionada."})


def list_offers(db: Session, supplier_id: int | None = None, product_id: int | None = None, season_id: int | None = None, collection_id: int | None = None, active_only: bool = False) -> list[dict[str, object]]:
    statement = _offer_query().join(ProductVariant, SupplierSupplyOffer.product_variant_id == ProductVariant.id).order_by(SupplierSupplyOffer.updated_at.desc(), SupplierSupplyOffer.id.desc())
    if supplier_id is not None:
        statement = statement.where(SupplierSupplyOffer.supplier_id == supplier_id)
    if product_id is not None:
        statement = statement.where(ProductVariant.product_id == product_id)
    if season_id is not None:
        statement = statement.where(SupplierSupplyOffer.season_id == season_id)
    if collection_id is not None:
        statement = statement.where(SupplierSupplyOffer.collection_id == collection_id)
    if active_only:
        statement = statement.where(SupplierSupplyOffer.is_active.is_(True))
    return [serialize_offer(offer) for offer in db.scalars(statement).all()]


def create_offer(db: Session, supplier_id: int, data: SupplyOfferCreateRequest) -> SupplierSupplyOffer:
    _validate_offer_references(db, supplier_id, data.product_variant_id, data.season_id, data.collection_id)
    duplicate = db.scalar(select(SupplierSupplyOffer.id).where(
        SupplierSupplyOffer.supplier_id == supplier_id,
        SupplierSupplyOffer.product_variant_id == data.product_variant_id,
        SupplierSupplyOffer.season_id == data.season_id,
        SupplierSupplyOffer.collection_id == data.collection_id,
    ))
    if duplicate:
        raise _conflict("Ya existe una oferta para el proveedor, variante, temporada y colección indicados.")
    offer = SupplierSupplyOffer(supplier_id=supplier_id, **data.model_dump())
    db.add(offer)
    db.flush()
    return get_offer(db, offer.id)


def update_offer(db: Session, offer: SupplierSupplyOffer, data: SupplyOfferAdminUpdateRequest) -> SupplierSupplyOffer:
    values = data.model_dump(exclude_unset=True)
    variant_id = values.get("product_variant_id", offer.product_variant_id)
    season_id = values.get("season_id", offer.season_id)
    collection_id = values.get("collection_id", offer.collection_id)
    if {variant_id, season_id, collection_id} != {offer.product_variant_id, offer.season_id, offer.collection_id}:
        _validate_offer_references(db, offer.supplier_id, variant_id, season_id, collection_id)
        duplicate = db.scalar(select(SupplierSupplyOffer.id).where(
            SupplierSupplyOffer.supplier_id == offer.supplier_id,
            SupplierSupplyOffer.product_variant_id == variant_id,
            SupplierSupplyOffer.season_id == season_id,
            SupplierSupplyOffer.collection_id == collection_id,
            SupplierSupplyOffer.id != offer.id,
        ))
        if duplicate:
            raise _conflict("Ya existe una oferta con la misma asociación.")
    for field, value in values.items():
        setattr(offer, field, value)
    db.flush()
    return get_offer(db, offer.id)


def update_supplier_offer(db: Session, offer: SupplierSupplyOffer, data: SupplyOfferSupplierUpdateRequest) -> SupplierSupplyOffer:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(offer, field, value)
    db.flush()
    return get_offer(db, offer.id, offer.supplier_id)

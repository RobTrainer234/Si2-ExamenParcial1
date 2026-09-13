from math import ceil
from pathlib import Path
import re
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.models import Category, Collection, Color, Product, ProductImage, ProductSupplier, ProductVariant, Season, Size, Supplier
from app.modules.products.schemas import ImageInput, ProductCreateRequest, ProductUpdateRequest, VariantInput


def _error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _conflict(message: str) -> HTTPException:
    return _error("PRODUCT_CONFLICT", message, status.HTTP_409_CONFLICT)


def _get_product_query(product_id: int):
    return select(Product).options(
        selectinload(Product.category),
        selectinload(Product.season),
        selectinload(Product.collection),
        selectinload(Product.variants).selectinload(ProductVariant.size),
        selectinload(Product.variants).selectinload(ProductVariant.color),
        selectinload(Product.images),
        selectinload(Product.suppliers),
    ).where(Product.id == product_id)


def get_product(db: Session, product_id: int) -> Product:
    product = db.scalar(_get_product_query(product_id))
    if product is None:
        raise _error("PRODUCT_NOT_FOUND", "Producto no encontrado.", status.HTTP_404_NOT_FOUND)
    return product


def serialize_variant(variant: ProductVariant) -> dict[str, object]:
    return {"id": variant.id, "size_id": variant.size_id, "size_name": variant.size.name, "size_type": variant.size.size_type, "sort_order": variant.size.sort_order, "color_id": variant.color_id, "color_name": variant.color.name, "sku": variant.sku, "is_active": variant.is_active}


def serialize_product(product: Product) -> dict[str, object]:
    return {
        "id": product.id,
        "category_id": product.category_id,
        "season_id": product.season_id,
        "collection_id": product.collection_id,
        "audience": product.audience,
        "size_system": product.size_system,
        "category_name": product.category.name,
        "code": product.code,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "is_active": product.is_active,
        "variants": [serialize_variant(variant) for variant in sorted(product.variants, key=lambda value: (value.size.sort_order, value.color.name, value.id))],
        "images": [{"id": image.id, "image_url": image.image_url, "is_primary": image.is_primary, "sort_order": image.sort_order} for image in sorted(product.images, key=lambda value: value.sort_order)],
        "supplier_ids": [link.supplier_id for link in product.suppliers],
    }


def serialize_summary(product: Product) -> dict[str, object]:
    return {"id": product.id, "category_id": product.category_id, "category_name": product.category.name, "audience": product.audience, "size_system": product.size_system, "code": product.code, "name": product.name, "slug": product.slug, "price": product.price, "is_active": product.is_active, "variant_count": len(product.variants)}


def list_products(db: Session, page: int, page_size: int, query: str | None, category_id: int | None) -> dict[str, object]:
    statement = select(Product).options(selectinload(Product.category), selectinload(Product.variants)).order_by(Product.name)
    count_statement = select(func.count(Product.id))
    if query:
        search = f"%{query.strip()}%"
        condition = or_(Product.name.ilike(search), Product.code.ilike(search), Product.slug.ilike(search))
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if category_id is not None:
        statement = statement.where(Product.category_id == category_id)
        count_statement = count_statement.where(Product.category_id == category_id)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_summary(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def _active_category(db: Session, category_id: int) -> Category:
    category = db.scalar(select(Category).where(Category.id == category_id, Category.is_active.is_(True)))
    if category is None:
        raise _error("CATEGORY_NOT_FOUND_OR_INACTIVE", "La categoría no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    return category


def _active_sizes_colors(db: Session, variants: list[VariantInput], size_system: str | None = None) -> None:
    size_ids = {variant.size_id for variant in variants}
    color_ids = {variant.color_id for variant in variants}
    size_rows = db.scalars(select(Size).where(Size.id.in_(size_ids), Size.is_active.is_(True))).all() if size_ids else []
    sizes = {size.id for size in size_rows}
    colors = set(db.scalars(select(Color.id).where(Color.id.in_(color_ids), Color.is_active.is_(True))).all()) if color_ids else set()
    if sizes != size_ids:
        raise _error("SIZE_NOT_FOUND_OR_INACTIVE", "Una o más tallas no existen o están inactivas.", status.HTTP_400_BAD_REQUEST)
    if size_system is not None and any(size.size_type != size_system for size in size_rows):
        raise _error("SIZE_SYSTEM_MISMATCH", "Una o más tallas no corresponden al sistema de tallas del producto.", status.HTTP_400_BAD_REQUEST)
    if colors != color_ids:
        raise _error("COLOR_NOT_FOUND_OR_INACTIVE", "Uno o más colores no existen o están inactivos.", status.HTTP_400_BAD_REQUEST)
    attributes = [(variant.size_id, variant.color_id) for variant in variants]
    if len(attributes) != len(set(attributes)):
        raise _conflict("No se puede repetir la combinación de talla y color.")
    skus = [variant.sku for variant in variants if variant.sku]
    if len(skus) != len(set(skus)):
        raise _conflict("No se puede repetir un SKU en el mismo producto.")


def _sku_part(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]+", "-", value.upper().strip(), flags=re.IGNORECASE)).strip("-")


def _materialize_variant_skus(db: Session, product_code: str, variants: list[VariantInput]) -> list[VariantInput]:
    size_ids = {variant.size_id for variant in variants}
    color_ids = {variant.color_id for variant in variants}
    size_names = {item.id: item.name for item in db.scalars(select(Size).where(Size.id.in_(size_ids))).all()}
    color_names = {item.id: item.name for item in db.scalars(select(Color).where(Color.id.in_(color_ids))).all()}
    used_skus = set(db.scalars(select(ProductVariant.sku)).all())
    generated_skus: set[str] = set()
    result: list[VariantInput] = []
    for variant in variants:
        if variant.sku:
            result.append(variant)
            generated_skus.add(variant.sku)
            continue
        base = _sku_part(f"{product_code}-{size_names.get(variant.size_id, variant.size_id)}-{color_names.get(variant.color_id, variant.color_id)}")[:74].rstrip("-")
        sku = base
        suffix = 2
        while sku in used_skus or sku in generated_skus:
            suffix_text = f"-{suffix}"
            sku = f"{base[:80 - len(suffix_text)]}{suffix_text}"
            suffix += 1
        generated_skus.add(sku)
        result.append(variant.model_copy(update={"sku": sku}))
    return result


def _active_suppliers(db: Session, supplier_ids: list[int]) -> None:
    unique_ids = set(supplier_ids)
    if len(unique_ids) != len(supplier_ids):
        raise _conflict("No se puede repetir un proveedor.")
    active_ids = set(db.scalars(select(Supplier.id).where(Supplier.id.in_(unique_ids), Supplier.is_active.is_(True))).all()) if unique_ids else set()
    if active_ids != unique_ids:
        raise _error("SUPPLIER_NOT_FOUND_OR_INACTIVE", "Uno o más proveedores no existen o están inactivos.", status.HTTP_400_BAD_REQUEST)


def _validate_season_collection(db: Session, season_id: int | None, collection_id: int | None) -> None:
    season = None
    if season_id is not None:
        season = db.scalar(select(Season).where(Season.id == season_id, Season.is_active.is_(True)))
        if season is None:
            raise _error("SEASON_NOT_FOUND_OR_INACTIVE", "La temporada no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    if collection_id is not None:
        collection = db.scalar(select(Collection).where(Collection.id == collection_id, Collection.is_active.is_(True)))
        if collection is None:
            raise _error("COLLECTION_NOT_FOUND_OR_INACTIVE", "La colección no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
        if season_id != collection.season_id:
            raise _error("COLLECTION_SEASON_MISMATCH", "La colección no pertenece a la temporada seleccionada.", status.HTTP_400_BAD_REQUEST)


def _add_relations(db: Session, product: Product, variants: list[VariantInput], images: list[ImageInput], supplier_ids: list[int]) -> None:
    for variant in variants:
        product.variants.append(ProductVariant(size_id=variant.size_id, color_id=variant.color_id, sku=variant.sku, is_active=variant.is_active))
    for image in images:
        product.images.append(ProductImage(image_url=str(image.image_url), is_primary=image.is_primary, sort_order=image.sort_order))
    for supplier_id in supplier_ids:
        product.suppliers.append(ProductSupplier(supplier_id=supplier_id))


def create_product(db: Session, data: ProductCreateRequest) -> Product:
    _active_category(db, data.category_id)
    _validate_season_collection(db, data.season_id, data.collection_id)
    variants = _materialize_variant_skus(db, data.code, data.variants)
    _active_sizes_colors(db, variants, data.size_system)
    _active_suppliers(db, data.supplier_ids)
    if sum(image.is_primary for image in data.images) > 1:
        raise _conflict("Un producto no puede tener más de una imagen principal.")
    if len({image.sort_order for image in data.images}) != len(data.images):
        raise _conflict("El orden de las imágenes no puede repetirse.")
    product = Product(category_id=data.category_id, season_id=data.season_id, collection_id=data.collection_id, audience=data.audience, size_system=data.size_system, code=data.code, name=data.name, slug=data.slug, description=data.description, price=data.price)
    db.add(product)
    try:
        db.flush()
        _add_relations(db, product, variants, data.images, data.supplier_ids)
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("El código, slug, SKU o relación indicada ya existe.") from exc
    return get_product(db, product.id)


def update_product(db: Session, product: Product, data: ProductUpdateRequest) -> Product:
    values = data.model_dump(exclude_unset=True)
    if "category_id" in values:
        _active_category(db, values["category_id"])
    if "season_id" in values or "collection_id" in values:
        _validate_season_collection(db, values.get("season_id", product.season_id), values.get("collection_id", product.collection_id))
    if "supplier_ids" in values:
        _active_suppliers(db, values["supplier_ids"] or [])
        product.suppliers.clear()
        product.suppliers.extend(ProductSupplier(supplier_id=supplier_id) for supplier_id in values.pop("supplier_ids") or [])
    if "size_system" in values:
        _active_sizes_colors(db, [VariantInput(size_id=variant.size_id, color_id=variant.color_id, sku=variant.sku, is_active=variant.is_active) for variant in product.variants], values["size_system"])
    for field, value in values.items():
        setattr(product, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("El código o slug ya existe.") from exc
    return get_product(db, product.id)


def set_product_active(db: Session, product: Product, active: bool) -> Product:
    product.is_active = active
    db.flush()
    return get_product(db, product.id)


def add_variant(db: Session, product: Product, data: VariantInput) -> Product:
    selected_size = db.scalar(select(Size).where(Size.id == data.size_id, Size.is_active.is_(True)))
    if selected_size is not None and not product.variants:
        product.size_system = selected_size.size_type
    _active_sizes_colors(db, [data], product.size_system)
    data = _materialize_variant_skus(db, product.code, [data])[0]
    if db.scalar(select(ProductVariant.id).where(ProductVariant.sku == data.sku)):
        raise _conflict("El SKU ya está registrado.")
    if db.scalar(select(ProductVariant.id).where(ProductVariant.product_id == product.id, ProductVariant.size_id == data.size_id, ProductVariant.color_id == data.color_id)):
        raise _conflict("La combinación de talla y color ya existe para el producto.")
    product.variants.append(ProductVariant(size_id=data.size_id, color_id=data.color_id, sku=data.sku, is_active=data.is_active))
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("El SKU o la combinación de variante ya existe.") from exc
    return get_product(db, product.id)


def add_variants_bulk(db: Session, product: Product, variants: list[VariantInput]) -> Product:
    if not variants:
        raise _error("VARIANTS_REQUIRED", "Debes seleccionar al menos una talla.", status.HTTP_400_BAD_REQUEST)
    if not product.variants:
        first_size = db.scalar(select(Size).where(Size.id == variants[0].size_id, Size.is_active.is_(True)))
        if first_size is not None:
            product.size_system = first_size.size_type
    _active_sizes_colors(db, variants, product.size_system)
    variants = _materialize_variant_skus(db, product.code, variants)
    existing_attributes = {(item.size_id, item.color_id) for item in product.variants}
    existing_skus = {item.sku for item in product.variants}
    incoming_attributes = [(item.size_id, item.color_id) for item in variants]
    incoming_skus = [item.sku for item in variants]
    if len(incoming_attributes) != len(set(incoming_attributes)) or any(item in existing_attributes for item in incoming_attributes):
        raise _conflict("Una o más combinaciones de talla y color ya existen para el producto.")
    if len(incoming_skus) != len(set(incoming_skus)) or any(item in existing_skus for item in incoming_skus) or db.scalar(select(ProductVariant.id).where(ProductVariant.sku.in_(incoming_skus))):
        raise _conflict("Uno o más SKU ya están registrados.")
    for variant in variants:
        product.variants.append(ProductVariant(size_id=variant.size_id, color_id=variant.color_id, sku=variant.sku, is_active=variant.is_active))
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("El SKU o la combinación de variante ya existe.") from exc
    return get_product(db, product.id)


def add_image(db: Session, product: Product, data: ImageInput) -> Product:
    if data.is_primary and any(image.is_primary for image in product.images):
        raise _conflict("El producto ya tiene una imagen principal.")
    if any(image.sort_order == data.sort_order for image in product.images):
        raise _conflict("El orden de la imagen ya está ocupado.")
    product.images.append(ProductImage(image_url=str(data.image_url), is_primary=data.is_primary, sort_order=data.sort_order))
    db.flush()
    return get_product(db, product.id)


def add_uploaded_image(db: Session, product: Product, image_url: str, is_primary: bool, sort_order: int) -> Product:
    if is_primary and any(image.is_primary for image in product.images):
        raise _conflict("El producto ya tiene una imagen principal.")
    if any(image.sort_order == sort_order for image in product.images):
        raise _conflict("El orden de la imagen ya está ocupado.")
    product.images.append(ProductImage(image_url=image_url, is_primary=is_primary, sort_order=sort_order))
    db.flush()
    return get_product(db, product.id)


def update_image(db: Session, product: Product, image_id: int, is_primary: bool | None, sort_order: int | None) -> Product:
    image = next((item for item in product.images if item.id == image_id), None)
    if image is None:
        raise _error("IMAGE_NOT_FOUND", "La imagen no existe para este producto.", status.HTTP_404_NOT_FOUND)
    if sort_order is not None and sort_order != image.sort_order and any(item.sort_order == sort_order for item in product.images):
        raise _conflict("El orden de la imagen ya está ocupado.")
    if is_primary is True:
        for item in product.images:
            item.is_primary = item.id == image_id
    elif is_primary is False:
        image.is_primary = False
    if sort_order is not None:
        image.sort_order = sort_order
    db.flush()
    return get_product(db, product.id)


def delete_image(db: Session, product: Product, image_id: int) -> tuple[Product, str | None]:
    image = next((item for item in product.images if item.id == image_id), None)
    if image is None:
        raise _error("IMAGE_NOT_FOUND", "La imagen no existe para este producto.", status.HTTP_404_NOT_FOUND)
    image_url = image.image_url
    db.delete(image)
    db.flush()
    return get_product(db, product.id), image_url


def uploaded_image_name(content_type: str | None, data: bytes, media_root: Path) -> tuple[str, Path]:
    signatures = {
        "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
        "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
        "image/webp": (b"RIFF", ".webp"),
    }
    image_type = signatures.get(content_type or "")
    if image_type is None or not data.startswith(image_type[0]) or (content_type == "image/webp" and data[8:12] != b"WEBP"):
        raise _error("UNSUPPORTED_IMAGE", "Solo se permiten imágenes JPG, PNG o WebP válidas.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    media_root.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{image_type[1]}"
    destination = media_root / filename
    destination.write_bytes(data)
    return f"/media/products/{filename}", destination

from math import ceil
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.models import Category, Color, Product, ProductImage, ProductSupplier, ProductVariant, Size, Supplier
from app.modules.products.schemas import ImageInput, ProductCreateRequest, ProductUpdateRequest, VariantInput


def _error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _conflict(message: str) -> HTTPException:
    return _error("PRODUCT_CONFLICT", message, status.HTTP_409_CONFLICT)


def _get_product_query(product_id: int):
    return select(Product).options(
        selectinload(Product.category),
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
    return {"id": variant.id, "size_id": variant.size_id, "size_name": variant.size.name, "color_id": variant.color_id, "color_name": variant.color.name, "sku": variant.sku, "is_active": variant.is_active}


def serialize_product(product: Product) -> dict[str, object]:
    return {
        "id": product.id,
        "category_id": product.category_id,
        "category_name": product.category.name,
        "code": product.code,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "is_active": product.is_active,
        "variants": [serialize_variant(variant) for variant in sorted(product.variants, key=lambda value: value.id)],
        "images": [{"id": image.id, "image_url": image.image_url, "is_primary": image.is_primary, "sort_order": image.sort_order} for image in sorted(product.images, key=lambda value: value.sort_order)],
        "supplier_ids": [link.supplier_id for link in product.suppliers],
    }


def serialize_summary(product: Product) -> dict[str, object]:
    return {"id": product.id, "category_id": product.category_id, "category_name": product.category.name, "code": product.code, "name": product.name, "slug": product.slug, "price": product.price, "is_active": product.is_active}


def list_products(db: Session, page: int, page_size: int, query: str | None, category_id: int | None) -> dict[str, object]:
    statement = select(Product).options(selectinload(Product.category)).order_by(Product.name)
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


def _active_sizes_colors(db: Session, variants: list[VariantInput]) -> None:
    size_ids = {variant.size_id for variant in variants}
    color_ids = {variant.color_id for variant in variants}
    sizes = set(db.scalars(select(Size.id).where(Size.id.in_(size_ids), Size.is_active.is_(True))).all()) if size_ids else set()
    colors = set(db.scalars(select(Color.id).where(Color.id.in_(color_ids), Color.is_active.is_(True))).all()) if color_ids else set()
    if sizes != size_ids:
        raise _error("SIZE_NOT_FOUND_OR_INACTIVE", "Una o más tallas no existen o están inactivas.", status.HTTP_400_BAD_REQUEST)
    if colors != color_ids:
        raise _error("COLOR_NOT_FOUND_OR_INACTIVE", "Uno o más colores no existen o están inactivos.", status.HTTP_400_BAD_REQUEST)
    attributes = [(variant.size_id, variant.color_id) for variant in variants]
    if len(attributes) != len(set(attributes)):
        raise _conflict("No se puede repetir la combinación de talla y color.")
    skus = [variant.sku for variant in variants]
    if len(skus) != len(set(skus)):
        raise _conflict("No se puede repetir un SKU en el mismo producto.")


def _active_suppliers(db: Session, supplier_ids: list[int]) -> None:
    unique_ids = set(supplier_ids)
    if len(unique_ids) != len(supplier_ids):
        raise _conflict("No se puede repetir un proveedor.")
    active_ids = set(db.scalars(select(Supplier.id).where(Supplier.id.in_(unique_ids), Supplier.is_active.is_(True))).all()) if unique_ids else set()
    if active_ids != unique_ids:
        raise _error("SUPPLIER_NOT_FOUND_OR_INACTIVE", "Uno o más proveedores no existen o están inactivos.", status.HTTP_400_BAD_REQUEST)


def _add_relations(db: Session, product: Product, variants: list[VariantInput], images: list[ImageInput], supplier_ids: list[int]) -> None:
    for variant in variants:
        product.variants.append(ProductVariant(size_id=variant.size_id, color_id=variant.color_id, sku=variant.sku, is_active=variant.is_active))
    for image in images:
        product.images.append(ProductImage(image_url=str(image.image_url), is_primary=image.is_primary, sort_order=image.sort_order))
    for supplier_id in supplier_ids:
        product.suppliers.append(ProductSupplier(supplier_id=supplier_id))


def create_product(db: Session, data: ProductCreateRequest) -> Product:
    _active_category(db, data.category_id)
    _active_sizes_colors(db, data.variants)
    _active_suppliers(db, data.supplier_ids)
    if sum(image.is_primary for image in data.images) > 1:
        raise _conflict("Un producto no puede tener más de una imagen principal.")
    if len({image.sort_order for image in data.images}) != len(data.images):
        raise _conflict("El orden de las imágenes no puede repetirse.")
    product = Product(category_id=data.category_id, code=data.code, name=data.name, slug=data.slug, description=data.description, price=data.price)
    db.add(product)
    try:
        db.flush()
        _add_relations(db, product, data.variants, data.images, data.supplier_ids)
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("El código, slug, SKU o relación indicada ya existe.") from exc
    return get_product(db, product.id)


def update_product(db: Session, product: Product, data: ProductUpdateRequest) -> Product:
    values = data.model_dump(exclude_unset=True)
    if "category_id" in values:
        _active_category(db, values["category_id"])
    if "supplier_ids" in values:
        _active_suppliers(db, values["supplier_ids"] or [])
        product.suppliers.clear()
        product.suppliers.extend(ProductSupplier(supplier_id=supplier_id) for supplier_id in values.pop("supplier_ids") or [])
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
    _active_sizes_colors(db, [data])
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


def add_image(db: Session, product: Product, data: ImageInput) -> Product:
    if data.is_primary and any(image.is_primary for image in product.images):
        raise _conflict("El producto ya tiene una imagen principal.")
    if any(image.sort_order == data.sort_order for image in product.images):
        raise _conflict("El orden de la imagen ya está ocupado.")
    product.images.append(ProductImage(image_url=str(data.image_url), is_primary=data.is_primary, sort_order=data.sort_order))
    db.flush()
    return get_product(db, product.id)

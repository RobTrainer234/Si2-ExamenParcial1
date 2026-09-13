from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.models import Branch, Category, City, Collection, Color, Inventory, Product, ProductVariant, Season, Size


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "PRODUCT_NOT_FOUND", "message": "Producto no encontrado."})


def _base_product_statement():
    return select(Product).join(Category, Product.category_id == Category.id).where(Product.is_active.is_(True), Category.is_active.is_(True))


def _base_count_statement():
    return select(func.count(distinct(Product.id))).join(Category, Product.category_id == Category.id).where(Product.is_active.is_(True), Category.is_active.is_(True))


def _apply_filters(statement, count_statement, query: str | None, category_id: int | None, size_id: int | None, color_id: int | None, branch_id: int | None, audience: str | None, season_id: int | None, collection_id: int | None):
    if query:
        search = f"%{query.strip()}%"
        condition = or_(Product.name.ilike(search), Product.code.ilike(search), Product.slug.ilike(search))
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if category_id is not None:
        condition = Product.category_id == category_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if audience is not None:
        condition = Product.audience == audience
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if season_id is not None:
        condition = Product.season_id == season_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if collection_id is not None:
        condition = Product.collection_id == collection_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    needs_variant = size_id is not None or color_id is not None or branch_id is not None
    if needs_variant:
        statement = statement.join(ProductVariant, ProductVariant.product_id == Product.id).where(ProductVariant.is_active.is_(True))
        count_statement = count_statement.join(ProductVariant, ProductVariant.product_id == Product.id).where(ProductVariant.is_active.is_(True))
        if size_id is not None:
            statement = statement.where(ProductVariant.size_id == size_id)
            count_statement = count_statement.where(ProductVariant.size_id == size_id)
        if color_id is not None:
            statement = statement.where(ProductVariant.color_id == color_id)
            count_statement = count_statement.where(ProductVariant.color_id == color_id)
        if branch_id is not None:
            statement = statement.join(Inventory, Inventory.product_variant_id == ProductVariant.id).join(Branch, Inventory.branch_id == Branch.id).join(City, Branch.city_id == City.id).where(Inventory.stock_quantity - Inventory.reserved_quantity > 0, Branch.id == branch_id, Branch.is_active.is_(True), City.is_active.is_(True))
            count_statement = count_statement.join(Inventory, Inventory.product_variant_id == ProductVariant.id).join(Branch, Inventory.branch_id == Branch.id).join(City, Branch.city_id == City.id).where(Inventory.stock_quantity - Inventory.reserved_quantity > 0, Branch.id == branch_id, Branch.is_active.is_(True), City.is_active.is_(True))
    return statement, count_statement


def _summary(product: Product) -> dict[str, object]:
    primary_image = next((image for image in sorted(product.images, key=lambda value: value.sort_order) if image.is_primary), None)
    if primary_image is None and product.images:
        primary_image = sorted(product.images, key=lambda value: value.sort_order)[0]
    return {"id": product.id, "category_id": product.category_id, "category_name": product.category.name, "audience": product.audience, "code": product.code, "name": product.name, "slug": product.slug, "price": product.price, "image_url": primary_image.image_url if primary_image else None}


def list_catalog(db: Session, page: int, page_size: int, query: str | None, category_id: int | None, size_id: int | None, color_id: int | None, branch_id: int | None, audience: str | None = None, season_id: int | None = None, collection_id: int | None = None, sort: str = "editorial") -> dict[str, object]:
    statement, count_statement = _apply_filters(_base_product_statement(), _base_count_statement(), query, category_id, size_id, color_id, branch_id, audience, season_id, collection_id)
    ordering = Product.created_at.desc() if sort == "newest" else Product.name
    statement = statement.options(selectinload(Product.category), selectinload(Product.images)).distinct().order_by(ordering)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [_summary(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def catalog_filters(db: Session) -> dict[str, list[dict[str, object]]]:
    categories = db.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.name)).all()
    sizes = db.scalars(select(Size).where(Size.is_active.is_(True)).order_by(Size.sort_order, Size.name)).all()
    colors = db.scalars(select(Color).where(Color.is_active.is_(True)).order_by(Color.name)).all()
    branches = db.scalars(select(Branch).join(City).where(Branch.is_active.is_(True), City.is_active.is_(True)).order_by(Branch.name)).all()
    audience_names = {"WOMEN": "Mujer", "MEN": "Hombre", "UNISEX": "Unisex"}
    audience_counts = dict(db.execute(select(Product.audience, func.count(Product.id)).join(Category).where(Product.is_active.is_(True), Category.is_active.is_(True)).group_by(Product.audience)).all())
    return {
        "categories": [{"id": item.id, "name": item.name} for item in categories],
        "sizes": [{"id": item.id, "name": item.name, "size_type": item.size_type, "sort_order": item.sort_order} for item in sizes],
        "colors": [{"id": item.id, "name": item.name, "hex_code": item.hex_code} for item in colors],
        "branches": [{"id": item.id, "name": item.name} for item in branches],
        "audiences": [{"code": code, "name": name, "product_count": audience_counts.get(code, 0)} for code, name in audience_names.items()],
    }


def catalog_navigation(db: Session) -> dict[str, object]:
    audience_names = {"WOMEN": "Mujer", "MEN": "Hombre", "UNISEX": "Unisex"}
    active_product = Product.is_active.is_(True)
    active_category = Category.is_active.is_(True)
    audience_counts = dict(db.execute(select(Product.audience, func.count(Product.id)).join(Category).where(active_product, active_category).group_by(Product.audience)).all())
    category_rows = db.execute(select(Category.id, Category.name).join(Product).where(active_category, active_product).distinct().order_by(Category.name)).all()
    season_rows = db.scalars(select(Season).where(Season.is_active.is_(True)).order_by(Season.starts_on.desc().nullslast(), Season.name)).all()
    collection_rows = db.execute(select(Collection.id, Collection.season_id, Collection.name, func.count(Product.id)).join(Product, Product.collection_id == Collection.id, isouter=True).where(Collection.is_active.is_(True), (Product.id.is_(None) | active_product)).group_by(Collection.id).order_by(Collection.name)).all()
    collections_by_season: dict[int, list[dict[str, object]]] = {}
    for collection_id, season_id, name, product_count in collection_rows:
        collections_by_season.setdefault(season_id, []).append({"id": collection_id, "name": name, "product_count": product_count})
    branches = db.scalars(select(Branch).join(City).where(Branch.is_active.is_(True), City.is_active.is_(True)).order_by(Branch.name)).all()
    return {
        "audiences": [{"code": code, "name": name, "product_count": audience_counts.get(code, 0)} for code, name in audience_names.items()],
        "categories": [{"id": item.id, "name": item.name} for item in category_rows],
        "seasons": [{"id": season.id, "name": season.name, "collections": collections_by_season.get(season.id, [])} for season in season_rows],
        "branches": [{"id": item.id, "name": item.name} for item in branches],
    }


def get_catalog_product(db: Session, product_id: int) -> Product:
    product = db.scalar(
        _base_product_statement().options(
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(ProductVariant.size),
            selectinload(Product.variants).selectinload(ProductVariant.color),
            selectinload(Product.variants).selectinload(ProductVariant.inventory),
            selectinload(Product.images),
        ).where(Product.id == product_id)
    )
    if product is None:
        raise _not_found()
    return product


def serialize_detail(product: Product) -> dict[str, object]:
    return {
        "id": product.id,
        "category_id": product.category_id,
        "category_name": product.category.name,
        "audience": product.audience,
        "size_system": product.size_system,
        "code": product.code,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "images": [{"image_url": image.image_url, "is_primary": image.is_primary, "sort_order": image.sort_order} for image in sorted(product.images, key=lambda value: value.sort_order)],
        "variants": [{"id": variant.id, "size_id": variant.size_id, "size_name": variant.size.name, "size_type": variant.size.size_type, "sort_order": variant.size.sort_order, "color_id": variant.color_id, "color_name": variant.color.name, "sku": variant.sku, "stock_total": sum(item.stock_quantity - item.reserved_quantity for item in variant.inventory), "available": any(item.stock_quantity - item.reserved_quantity > 0 for item in variant.inventory)} for variant in sorted(product.variants, key=lambda value: (value.size.sort_order, value.color.name, value.id)) if variant.is_active],
    }


def availability(db: Session, product_id: int, size_id: int, color_id: int) -> list[dict[str, object]]:
    statement = (
        select(Inventory, Branch, City)
        .join(ProductVariant, Inventory.product_variant_id == ProductVariant.id)
        .join(Product, ProductVariant.product_id == Product.id)
        .join(Branch, Inventory.branch_id == Branch.id)
        .join(City, Branch.city_id == City.id)
        .where(
            Product.id == product_id,
            Product.is_active.is_(True),
            ProductVariant.size_id == size_id,
            ProductVariant.color_id == color_id,
            ProductVariant.is_active.is_(True),
            Branch.is_active.is_(True),
            City.is_active.is_(True),
        )
        .order_by(City.name, Branch.name)
    )
    if db.scalar(_base_product_statement().with_only_columns(Product.id).where(Product.id == product_id)) is None:
        raise _not_found()
    return [{"branch_id": item.branch_id, "branch_name": branch.name, "city_name": city.name, "address": branch.address, "available": item.stock_quantity - item.reserved_quantity > 0, "stock": item.stock_quantity - item.reserved_quantity} for item, branch, city in db.execute(statement).all()]

"""Clona el catálogo del tenant origen (Empresa Legado, id=1) a los demás tenants.

Copia por tenant: temporadas, colecciones, categorías, productos, imágenes,
variantes e inventario por sucursal (stock físico, reservas en 0).
Tallas y colores son globales y se reutilizan. Es idempotente: omite
tenants que ya tienen productos.

Uso (dentro del contenedor backend):
    python scripts/clone_catalog_to_tenants.py
"""
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.models import (
    Branch,
    Category,
    Collection,
    Inventory,
    Product,
    ProductImage,
    ProductVariant,
    Season,
    Tenant,
)

SOURCE_TENANT_ID = 1


def clone_for_tenant(db, target: Tenant) -> dict:
    src = SOURCE_TENANT_ID
    season_map, collection_map, category_map, product_map, variant_map = {}, {}, {}, {}, {}

    for s in db.scalars(select(Season).where(Season.tenant_id == src)):
        n = Season(tenant_id=target.id, name=s.name, starts_on=s.starts_on, ends_on=s.ends_on, is_active=s.is_active)
        db.add(n)
        db.flush()
        season_map[s.id] = n.id

    for c in db.scalars(select(Collection).where(Collection.tenant_id == src)):
        n = Collection(
            tenant_id=target.id,
            season_id=season_map.get(c.season_id),
            name=c.name,
            description=c.description,
            is_active=c.is_active,
        )
        db.add(n)
        db.flush()
        collection_map[c.id] = n.id

    for c in db.scalars(select(Category).where(Category.tenant_id == src)):
        n = Category(tenant_id=target.id, name=c.name, description=c.description, is_active=c.is_active)
        db.add(n)
        db.flush()
        category_map[c.id] = n.id

    for p in db.scalars(select(Product).where(Product.tenant_id == src).order_by(Product.id)):
        n = Product(
            tenant_id=target.id,
            category_id=category_map[p.category_id],
            season_id=season_map.get(p.season_id),
            collection_id=collection_map.get(p.collection_id),
            audience=p.audience,
            size_system=p.size_system,
            code=p.code,
            name=p.name,
            slug=p.slug,
            description=p.description,
            price=p.price,
            is_active=p.is_active,
        )
        db.add(n)
        db.flush()
        product_map[p.id] = n.id
        for img in db.scalars(select(ProductImage).where(ProductImage.product_id == p.id)):
            db.add(ProductImage(product_id=n.id, image_url=img.image_url, is_primary=img.is_primary, sort_order=img.sort_order))

    for v in db.scalars(select(ProductVariant).where(ProductVariant.tenant_id == src).order_by(ProductVariant.id)):
        n = ProductVariant(
            tenant_id=target.id,
            product_id=product_map[v.product_id],
            size_id=v.size_id,
            color_id=v.color_id,
            sku=v.sku,
            is_active=v.is_active,
        )
        db.add(n)
        db.flush()
        variant_map[v.id] = n.id

    # Inventario: cada sucursal destino toma el stock de una sucursal origen (round-robin).
    src_branches = db.scalars(select(Branch).where(Branch.tenant_id == src).order_by(Branch.id)).all()
    src_branches = [b for b in src_branches if db.scalar(select(Inventory.id).where(Inventory.branch_id == b.id).limit(1))]
    dst_branches = db.scalars(select(Branch).where(Branch.tenant_id == target.id).order_by(Branch.id)).all()
    inv_count = 0
    for i, dst in enumerate(dst_branches):
        src_branch = src_branches[i % len(src_branches)]
        for inv in db.scalars(select(Inventory).where(Inventory.branch_id == src_branch.id)):
            if inv.product_variant_id not in variant_map:
                continue
            db.add(Inventory(
                tenant_id=target.id,
                branch_id=dst.id,
                product_variant_id=variant_map[inv.product_variant_id],
                stock_quantity=max(inv.stock_quantity, 0),
                reserved_quantity=0,
            ))
            inv_count += 1

    return {
        "categorias": len(category_map),
        "productos": len(product_map),
        "variantes": len(variant_map),
        "sucursales": len(dst_branches),
        "inventario": inv_count,
    }


def main() -> None:
    db = SessionLocal()
    try:
        targets = db.scalars(select(Tenant).where(Tenant.id != SOURCE_TENANT_ID).order_by(Tenant.id)).all()
        for t in targets:
            if db.scalar(select(Product.id).where(Product.tenant_id == t.id).limit(1)):
                print(f"[omitido] Tenant {t.id} '{t.name}' ya tiene productos.")
                continue
            stats = clone_for_tenant(db, t)
            print(f"[ok] Tenant {t.id} '{t.name}': {stats}")
        db.commit()
        print("Clonación completada.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

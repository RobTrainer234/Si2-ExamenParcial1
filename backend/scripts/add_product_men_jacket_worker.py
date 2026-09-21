from datetime import date
from decimal import Decimal
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.models import (
    Product, ProductImage, ProductVariant, ProductSupplier,
    SupplierSupplyOffer, Inventory, Category, Season, Collection,
    Size, Color, Supplier, Branch
)

def register():
    db = SessionLocal()
    try:
        code = "MEN-CHQ-003"
        name = "Chaqueta Worker Canvas Ojetes Carbón"
        slug = "chaqueta-worker-canvas-ojetes-carbon"
        description = (
            "Cazadora de corte workwear confeccionada en resistente sarga canvas de algodón 100% con lavado mineral en gris carbón desgastado. "
            "Presenta cuello camisero estructurado, cierre frontal de cremallera metálica oculta con tapeta, bolsillo horizontal con cremallera en el pecho, "
            "bolsillos de vivo laterales ornamentados con hilera de ojetes metálicos plateados y un llamativo bordado tipográfico tonal en relieve a lo largo de la manga. "
            "Silueta recta holgada de estética utility urbana con trabillas ajustables en cintura."
        )
        price = Decimal("375.00")
        audience = "MEN"

        cat = db.get(Category, 13) or db.scalar(select(Category).where(Category.name.ilike("%chaqueta%")))
        cat_id = cat.id if cat else 13
        season = db.scalar(select(Season).where(Season.name.ilike("%esenciales%"))) or db.scalar(select(Season))
        season_id = season.id if season else 3
        coll = db.scalar(select(Collection).where(Collection.name.ilike("%nocturna%"))) or db.scalar(select(Collection))
        coll_id = coll.id if coll else 4

        # Check existing product
        product = db.scalar(select(Product).where(Product.code == code))
        if product is None:
            product = Product(
                category_id=cat_id,
                season_id=season_id,
                collection_id=coll_id,
                audience=audience,
                size_system="ALPHA",
                code=code,
                name=name,
                slug=slug,
                description=description,
                price=price,
                is_active=True
            )
            db.add(product)
            db.flush()
            print(f"Created product: {product.id} - {product.name}")
        else:
            product.category_id = cat_id
            product.season_id = season_id
            product.collection_id = coll_id
            product.name = name
            product.slug = slug
            product.description = description
            product.price = price
            product.audience = audience
            product.is_active = True
            db.flush()
            print(f"Updated existing product: {product.id}")

        # Supplier link: Textiles Andinos S.R.L.
        supplier = db.scalar(select(Supplier).where(Supplier.trade_name.ilike("%andinos%"))) or db.scalar(select(Supplier))
        if supplier:
            prod_sup = db.get(ProductSupplier, (product.id, supplier.id))
            if not prod_sup:
                db.add(ProductSupplier(product_id=product.id, supplier_id=supplier.id))
                db.flush()
                print(f"Linked supplier: {supplier.trade_name}")

        # Images (3 images: front, profile sleeve, back)
        image_data = [
            ("/media/products/chaqueta-worker-canvas-front.webp", True, 0),
            ("/media/products/chaqueta-worker-canvas-profile.webp", False, 1),
            ("/media/products/chaqueta-worker-canvas-back.webp", False, 2),
        ]
        for old_img in list(product.images):
            db.delete(old_img)
        db.flush()

        for url, is_primary, order in image_data:
            img = ProductImage(
                product_id=product.id,
                image_url=url,
                is_primary=is_primary,
                sort_order=order
            )
            db.add(img)
        db.flush()
        print("Registered 3 images (front, profile, back)")

        # Color: Gris Carbón (#38393D)
        color = db.scalar(select(Color).where(Color.name.ilike("%carbón%") | Color.name.ilike("%carbon%")))
        if not color:
            color = Color(name="Gris Carbón", hex_code="#38393D")
            db.add(color)
            db.flush()
            print(f"Created color: {color.id} - {color.name}")

        # Sizes: S, M, L, XL
        size_names = ["S", "M", "L", "XL"]
        sizes = []
        for s_name in size_names:
            sz = db.scalar(select(Size).where(Size.name == s_name, Size.size_type == "ALPHA"))
            if not sz:
                sz = db.scalar(select(Size).where(Size.name.ilike(f"%{s_name}%")))
            if sz:
                sizes.append(sz)

        branches = db.scalars(select(Branch).where(Branch.is_active.is_(True))).all()

        for size in sizes:
            sku = f"{code}-{size.name.replace(' ', '')}-CRB"
            variant = db.scalar(
                select(ProductVariant).where(
                    ProductVariant.product_id == product.id,
                    ProductVariant.size_id == size.id,
                    ProductVariant.color_id == color.id
                )
            )
            if not variant:
                variant = ProductVariant(
                    product_id=product.id,
                    size_id=size.id,
                    color_id=color.id,
                    sku=sku,
                    is_active=True
                )
                db.add(variant)
                db.flush()
                print(f"Created variant: {variant.sku}")

            # Supply offer
            if supplier:
                offer = db.scalar(select(SupplierSupplyOffer).where(
                    SupplierSupplyOffer.supplier_id == supplier.id,
                    SupplierSupplyOffer.product_variant_id == variant.id
                ))
                if not offer:
                    db.add(SupplierSupplyOffer(
                        supplier_id=supplier.id,
                        product_variant_id=variant.id,
                        season_id=product.season_id or 3,
                        collection_id=product.collection_id or 4,
                        status="AVAILABLE",
                        available_quantity=35,
                        expected_date=date(2026, 11, 20),
                        notes="Lote lona canvas reforzada con acabados de ojetes y bordado de manga."
                    ))

            # Stock in branches
            for branch in branches:
                inv = db.scalar(select(Inventory).where(
                    Inventory.branch_id == branch.id,
                    Inventory.product_variant_id == variant.id
                ))
                if not inv:
                    db.add(Inventory(
                        branch_id=branch.id,
                        product_variant_id=variant.id,
                        stock_quantity=8,
                        reserved_quantity=0
                    ))
                else:
                    if inv.stock_quantity < 4:
                        inv.stock_quantity = 8

        db.commit()
        print(f"SUCCESS: Registered {name} ({code}) with 3 images, {len(sizes)} variants across {len(branches)} branches.")
    except Exception as e:
        db.rollback()
        print("ERROR:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    register()

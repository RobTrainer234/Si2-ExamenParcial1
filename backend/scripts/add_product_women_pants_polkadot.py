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
        code = "WOM-PAN-003"
        name = "Jeans Wide Leg Lunares Marino"
        slug = "jeans-wide-leg-lunares-marino"
        description = (
            "Jeans de tiro alto y silueta palazzo extra wide leg confeccionados en sarga de puro algodón 100% en azul marino índigo "
            "con alegre estampado integral de lunares blancos polka dot. Cuenta con pernera ancha acampanada de caída ligera y fluida, "
            "diseño clásico de cinco bolsillos, cierre frontal con cremallera y botón metálico plateado. "
            "Una prenda de inspiración retro setentera con un toque gráfico chic y veraniego."
        )
        price = Decimal("280.00")
        audience = "WOMEN"

        cat = db.get(Category, 4) or db.scalar(select(Category).where(Category.name.ilike("%pantal%")))
        cat_id = cat.id if cat else 4
        season = db.scalar(select(Season).where(Season.name.ilike("%primavera%"))) or db.scalar(select(Season))
        season_id = season.id if season else 1
        coll = db.scalar(select(Collection).where(Collection.name.ilike("%luz de patio%"))) or db.scalar(select(Collection))
        coll_id = coll.id if coll else 2

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

        # Images (2 images: model front, studio back)
        image_data = [
            ("/media/products/jeans-lunares-wide-front.webp", True, 0),
            ("/media/products/jeans-lunares-wide-back.webp", False, 1),
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
        print("Registered 2 images (model front, studio back)")

        # Color: Azul marino (id 6, #26354A)
        color = db.scalar(select(Color).where(Color.name.ilike("%marino%")))
        if not color:
            color = db.scalar(select(Color).where(Color.id == 6))

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
            sku = f"{code}-{size.name.replace(' ', '')}-MAR"
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
                        season_id=product.season_id or 1,
                        collection_id=product.collection_id or 2,
                        status="AVAILABLE",
                        available_quantity=45,
                        expected_date=date(2026, 10, 20),
                        notes="Lote especial denim estampado lunares polka dot."
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
        print(f"SUCCESS: Registered {name} ({code}) with 2 images, {len(sizes)} variants across {len(branches)} branches.")
    except Exception as e:
        db.rollback()
        print("ERROR:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    register()

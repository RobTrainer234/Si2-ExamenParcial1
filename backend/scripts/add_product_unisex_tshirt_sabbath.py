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
        code = "UNI-POL-001"
        name = "Polera Gráfica Black Sabbath Blanca Unisex"
        slug = "polera-grafica-black-sabbath-blanca-unisex"
        description = (
            "Polera gráfica unisex de corte relajado confeccionada en fino jersey de puro algodón 100% transpirable en blanco óptico. "
            "Diseñada con cuello redondo acanalado reforzado, manga corta amplia con hombros caídos y doble serigrafía de alta definición: "
            "pequeño logotipo icónico de Black Sabbath con la criatura alada en el pecho y un llamativo estampado maxi trasero con el ángel caído "
            "sobre fondo tipográfico en damero morado. Un básico esencial de culto que fusiona la actitud del rock clásico con la estética skate contemporánea."
        )
        price = Decimal("165.00")
        audience = "UNISEX"

        cat = db.get(Category, 11) or db.scalar(select(Category).where(Category.name.ilike("%polera%")))
        cat_id = cat.id if cat else 11
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

        # Images (2 images: front, back)
        image_data = [
            ("/media/products/polera-black-sabbath-front.png", True, 0),
            ("/media/products/polera-black-sabbath-back.png", False, 1),
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
        print("Registered 2 images (front, back)")

        # Color: Blanco (id 11, #FFFFFF)
        color = db.scalar(select(Color).where(Color.name == "Blanco")) or db.scalar(select(Color).where(Color.id == 11))

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
            sku = f"{code}-{size.name.replace(' ', '')}-BLA"
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
                        available_quantity=50,
                        expected_date=date(2026, 10, 20),
                        notes="Lote especial cápsula rock skater unisex."
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

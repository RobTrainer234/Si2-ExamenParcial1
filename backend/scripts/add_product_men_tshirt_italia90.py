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
        code = "MEN-POL-004"
        name = "Polera Gráfica Italia 90 Vintage"
        slug = "polera-grafica-italia-90-vintage"
        description = (
            "Polera gráfica de estética retro futbolera 'blokecore' confeccionada en fino jersey de puro algodón 100% en tono blanco roto marfil. "
            "Presenta emblemático estampado frontal conmemorativo 'ITALIA 90' con el balón geométrico tricolor de la copa mundial, "
            "cuello redondo acanalado y mangas cortas rematadas con puño elástico de doble raya deportiva en contraste. "
            "Una prenda nostálgica de coleccionista con silueta regular fit perfecta para elevar cualquier estilismo urbano contemporáneo."
        )
        price = Decimal("160.00")
        audience = "MEN"

        cat = db.get(Category, 11) or db.scalar(select(Category).where(Category.name.ilike("%polera%")))
        cat_id = cat.id if cat else 11
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

        # Images (3 images: studio front, model, studio back)
        image_data = [
            ("/media/products/polera-italia-90-studio.jpg", True, 0),
            ("/media/products/polera-italia-90-model.jpg", False, 1),
            ("/media/products/polera-italia-90-back.jpg", False, 2),
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
        print("Registered 3 images (front, model, back)")

        # Color: Marfil (id 3, #F5F3F0)
        color = db.scalar(select(Color).where(Color.name == "Marfil")) or db.scalar(select(Color).where(Color.name.ilike("%marfil%")))

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
                        available_quantity=50,
                        expected_date=date(2026, 10, 18),
                        notes="Lote especial cápsula fútbol retro Italia 90."
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

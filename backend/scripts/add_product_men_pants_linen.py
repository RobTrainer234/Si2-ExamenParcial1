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
        code = "MEN-PAN-002"
        name = "Pantalón Jogger Lino Negro"
        slug = "pantalon-jogger-lino-negro"
        description = (
            "Pantalón relajado confeccionado en mezcla de lino rústico y algodón suave de caída fluida y tejido transpirable. "
            "Diseñado con cinturilla elástica con cordón ajustable al tono, bolsillos laterales insertados en costura y dos bolsillos traseros de ojal. "
            "Silueta straight fit moderna que fusiona la comodidad informal del jogger con la frescura noble del lino para los días cálidos."
        )
        price = Decimal("255.00")
        audience = "MEN"

        cat = db.get(Category, 4) or db.scalar(select(Category).where(Category.name.ilike("%pantal%")))
        cat_id = cat.id if cat else 4
        season = db.scalar(select(Season).where(Season.name.ilike("%primavera%") | Season.name.ilike("%esenciales%"))) or db.scalar(select(Season))
        season_id = season.id if season else 3
        coll = db.scalar(select(Collection).where(Collection.name.ilike("%luz de patio%"))) or db.scalar(select(Collection).where(Collection.name.ilike("%atelier%"))) or db.scalar(select(Collection))
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

        # Supplier link: Casa Lino Bolivia (id 2) or Textiles Andinos
        supplier = db.scalar(select(Supplier).where(Supplier.trade_name.ilike("%casa lino%"))) or db.scalar(select(Supplier))
        if supplier:
            prod_sup = db.get(ProductSupplier, (product.id, supplier.id))
            if not prod_sup:
                db.add(ProductSupplier(product_id=product.id, supplier_id=supplier.id))
                db.flush()
                print(f"Linked supplier: {supplier.trade_name}")

        # Images (3 images: studio front, model, studio back)
        image_data = [
            ("/media/products/pantalon-lino-jogger-studio.jpg", True, 0),
            ("/media/products/pantalon-lino-jogger-model.jpg", False, 1),
            ("/media/products/pantalon-lino-jogger-back.jpg", False, 2),
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
        print("Registered 3 images (studio, model, back)")

        # Color: Negro (id 2)
        color = db.scalar(select(Color).where(Color.name == "Negro")) or db.scalar(select(Color).where(Color.name.ilike("%negro%")))

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
            sku = f"{code}-{size.name.replace(' ', '')}-NEG"
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
                        expected_date=date(2026, 10, 10),
                        notes="Lote lino y algodón ligero con cordón ajustable."
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

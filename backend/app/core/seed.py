from datetime import date

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.models import Branch, Category, City, Collection, Color, Inventory, Permission, Product, ProductImage, ProductSupplier, ProductVariant, Role, Season, Size, Supplier, SupplierSupplyOffer, User
from app.core.security import hash_password

ROLES = {
    "ADMIN": "Administrador",
    "CLIENT": "Cliente",
    "BRANCH_MANAGER": "Encargado de sucursal",
    "CASHIER": "Cajero",
    "SUPPLIER": "Proveedor",
}

PERMISSIONS = {
    "catalog.read": "Consultar catálogo",
    "catalog.availability": "Consultar disponibilidad",
    "users.manage": "Gestionar usuarios y roles",
    "locations.manage": "Gestionar ciudades y sucursales",
    "masters.manage": "Gestionar catálogos maestros",
    "suppliers.manage": "Gestionar proveedores",
    "suppliers.portal": "Consultar portal de proveedor",
    "seasons.manage": "Gestionar temporadas y colecciones",
    "products.manage": "Gestionar productos",
    "products.publish": "Publicar productos",
    "inventory.read": "Consultar inventario",
    "inventory.adjust": "Ajustar inventario",
    "reservations.read": "Consultar reservas propias",
    "reservations.create": "Crear reservas propias",
    "reservations.cancel": "Cancelar reservas propias",
    "reservations.manage": "Gestionar reservas de sucursal",
    "cart.manage": "Gestionar carrito propio",
    "sales.read": "Consultar ventas",
    "sales.create": "Registrar ventas",
    "payments.cash": "Procesar pagos en caja",
    "payments.electronic": "Procesar pagos electronicos",
    "promotions.manage": "Gestionar promociones",
    "reports.read": "Consultar reportes",
    "recommendations.read": "Consultar recomendaciones",
    "virtual_fitting.use": "Usar vestidor virtual",
}

ROLE_PERMISSIONS = {
    "ADMIN": set(PERMISSIONS),
    "CLIENT": {"catalog.read", "catalog.availability", "reservations.read", "reservations.create", "reservations.cancel", "cart.manage", "sales.read", "payments.electronic", "recommendations.read", "virtual_fitting.use"},
    "BRANCH_MANAGER": {"catalog.read", "catalog.availability", "inventory.read", "inventory.adjust", "reservations.read", "reservations.manage", "sales.read"},
    "CASHIER": {"catalog.read", "catalog.availability", "inventory.read", "sales.read", "sales.create", "payments.cash"},
    "SUPPLIER": {"catalog.read", "suppliers.portal"},
}

DEMO_USERS = {
    "CLIENT": ("Cliente", "Demo", "client.demo@fashionstore.com", "70000001", "Client123!"),
    "BRANCH_MANAGER": ("Encargado", "Demo", "manager.demo@fashionstore.com", "70000002", "Manager123!"),
    "CASHIER": ("Cajero", "Demo", "cashier.demo@fashionstore.com", "70000003", "Cashier123!"),
    "SUPPLIER": ("Proveedor", "Demo", "supplier.demo@fashionstore.com", "70000004", "Supplier123!"),
}


def seed_development_data() -> None:
    if settings.app_env != "development":
        raise RuntimeError("El seed de desarrollo solo puede ejecutarse con APP_ENV=development")
    if not settings.seed_admin_password:
        raise RuntimeError("SEED_ADMIN_PASSWORD es obligatorio para ejecutar el seed")

    with SessionLocal.begin() as db:
        roles: dict[str, Role] = {}
        for code, name in ROLES.items():
            role = db.scalar(select(Role).where(Role.code == code))
            if role is None:
                role = Role(code=code, name=name)
                db.add(role)
                db.flush()
            roles[code] = role

        permissions: dict[str, Permission] = {}
        for code, name in PERMISSIONS.items():
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                permission = Permission(code=code, name=name)
                db.add(permission)
                db.flush()
            permissions[code] = permission
        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            roles[role_code].permissions = [permissions[code] for code in permission_codes]

        admin = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))
        if admin is None:
            db.add(
                User(
                    role=roles["ADMIN"],
                    first_name="Administrador",
                    last_name="FashionStore",
                    email=settings.seed_admin_email.lower(),
                    phone="000000000",
                    password_hash=hash_password(settings.seed_admin_password),
                )
            )

        # Keep demo users created by older seeds valid for the admin listing.
        for legacy_email in (
            "client.demo@fashionstore.local",
            "manager.demo@fashionstore.local",
            "cashier.demo@fashionstore.local",
            "client.demo@fashionstore.test",
            "manager.demo@fashionstore.test",
            "cashier.demo@fashionstore.test",
        ):
            legacy_user = db.scalar(select(User).where(User.email == legacy_email))
            if legacy_user is not None:
                local_part, domain = legacy_email.split("@", 1)
                legacy_domain = domain.split(".")[-1]
                legacy_user.email = f"legacy.{legacy_domain}.{local_part}@fashionstore.com"
                legacy_user.is_active = False

        cities = {}
        for city_name in ("Santa Cruz", "Cochabamba"):
            city = db.scalar(select(City).where(City.name == city_name))
            if city is None:
                city = City(name=city_name)
                db.add(city)
                db.flush()
            cities[city_name] = city

        branches = {}
        branch_data = (("Santa Cruz", "FashionStore Centro", "Av. Principal 100", "70001001"), ("Cochabamba", "FashionStore Norte", "Av. América 200", "70001002"))
        for city_name, branch_name, address, phone in branch_data:
            branch = db.scalar(select(Branch).where(Branch.city_id == cities[city_name].id, Branch.name == branch_name))
            if branch is None:
                branch = Branch(city_id=cities[city_name].id, name=branch_name, address=address, phone=phone)
                db.add(branch)
                db.flush()
            branches[branch_name] = branch

        supplier = db.scalar(select(Supplier).where(Supplier.tax_id == "DEMO-NIT-001"))
        if supplier is None:
            supplier = Supplier(trade_name="Textiles Andinos Demo", legal_name="Textiles Andinos S.R.L.", tax_id="DEMO-NIT-001", email="contacto@textilesandinos.com", phone="70002001", address="Parque Industrial, Santa Cruz")
            db.add(supplier)
            db.flush()

        for role_code, (first_name, last_name, email, phone, password) in DEMO_USERS.items():
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(role=roles[role_code], supplier=supplier if role_code == "SUPPLIER" else None, first_name=first_name, last_name=last_name, email=email, phone=phone, password_hash=hash_password(password))
                db.add(user)
                db.flush()
            if role_code == "BRANCH_MANAGER":
                if branches["FashionStore Centro"] not in user.branches:
                    user.branches.append(branches["FashionStore Centro"])
                if branches["FashionStore Norte"] not in user.branches:
                    user.branches.append(branches["FashionStore Norte"])
            if role_code == "CASHIER":
                if branches["FashionStore Norte"] not in user.branches:
                    user.branches.append(branches["FashionStore Norte"])

        categories = {}
        for category_name, description in (("Demo Abrigos", "Prendas de demostración para validar el Ciclo 2"), ("Demo Camisas", "Camisas y blusas para pruebas del catálogo"), ("Demo Pantalones", "Pantalones para pruebas de disponibilidad")):
            category = db.scalar(select(Category).where(Category.name == category_name))
            if category is None:
                category = Category(name=category_name, description=description)
                db.add(category)
                db.flush()
            categories[category_name] = category
        sizes = {}
        for size_name, sort_order in (("Demo S", 20), ("Demo M", 30), ("Demo L", 40)):
            size = db.scalar(select(Size).where(Size.name == size_name))
            if size is None:
                size = Size(name=size_name, size_type="ALPHA", sort_order=sort_order)
                db.add(size)
                db.flush()
            sizes[size_name] = size
        colors = {}
        for color_name, hex_code in (("Demo Negro", "#171717"), ("Demo Azul", "#244b74"), ("Demo Beige", "#d8c3a5")):
            color = db.scalar(select(Color).where(Color.name == color_name))
            if color is None:
                color = Color(name=color_name, hex_code=hex_code)
                db.add(color)
                db.flush()
            colors[color_name] = color
        season = db.scalar(select(Season).where(Season.name == "Demo Primavera-Verano 2026"))
        if season is None:
            season = Season(name="Demo Primavera-Verano 2026", starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31))
            db.add(season)
            db.flush()
        collection = db.scalar(select(Collection).where(Collection.season_id == season.id, Collection.name == "Demo Esenciales"))
        if collection is None:
            collection = Collection(season_id=season.id, name="Demo Esenciales", description="Colección demo para pruebas de catálogo, reservas y ventas")
            db.add(collection)
            db.flush()

        products = (("DEMO-ABR-001", "Abrigo Demo Atelier", "abrigo-demo-atelier", 450, "Demo Abrigos", "Prenda abrigada de corte recto, confeccionada para la colección de temporada."), ("DEMO-ABR-002", "Chaqueta Demo Urbana", "chaqueta-demo-urbana", 380, "Demo Abrigos", "Chaqueta ligera con acabado urbano y bolsillos funcionales."), ("DEMO-CAM-001", "Camisa Demo Oxford", "camisa-demo-oxford", 220, "Demo Camisas", "Camisa versátil de algodón para uso diario."))
        for code, name, slug, price, category_name, description in products:
            product = db.scalar(select(Product).where(Product.code == code))
            if product is None:
                product = Product(category_id=categories[category_name].id, season_id=season.id, collection_id=collection.id, audience="UNISEX", size_system="ALPHA", code=code, name=name, slug=slug, description=description, price=price)
                db.add(product)
                db.flush()
            product_supplier = db.get(ProductSupplier, (product.id, supplier.id))
            if product_supplier is None:
                db.add(ProductSupplier(product_id=product.id, supplier_id=supplier.id))
            image = db.scalar(select(ProductImage).where(ProductImage.product_id == product.id, ProductImage.sort_order == 0))
            if not product.description:
                product.description = description
            if image is None:
                image_urls = ("https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3", "https://images.unsplash.com/photo-1542291026-7eec264c27ff", "https://images.unsplash.com/photo-1525507119028-ed4c629a60a3")
                db.add(ProductImage(product_id=product.id, image_url=f"{image_urls[len(product.variants) % len(image_urls)]}?auto=format&fit=crop&w=800&q=80", is_primary=True, sort_order=0))
            for size_name, color_name, stock in (("Demo S", "Demo Negro", 6), ("Demo M", "Demo Negro", 8), ("Demo M", "Demo Azul", 10)):
                variant = db.scalar(select(ProductVariant).where(ProductVariant.product_id == product.id, ProductVariant.size_id == sizes[size_name].id, ProductVariant.color_id == colors[color_name].id))
                if variant is None:
                    variant = ProductVariant(product_id=product.id, size_id=sizes[size_name].id, color_id=colors[color_name].id, sku=f"{code}-{size_name.split()[-1]}-{color_name.split()[-1].upper()}")
                    db.add(variant)
                    db.flush()
                offer = db.scalar(select(SupplierSupplyOffer).where(SupplierSupplyOffer.supplier_id == supplier.id, SupplierSupplyOffer.product_variant_id == variant.id))
                if offer is None:
                    db.add(SupplierSupplyOffer(supplier_id=supplier.id, product_variant_id=variant.id, season_id=season.id, collection_id=collection.id, status="AVAILABLE", available_quantity=25, expected_date=date(2026, 10, 15), notes="Oferta demo para pruebas de abastecimiento."))
                for branch_name, branch_stock in (("FashionStore Centro", stock), ("FashionStore Norte", stock + 4)):
                    inventory = db.scalar(select(Inventory).where(Inventory.branch_id == branches[branch_name].id, Inventory.product_variant_id == variant.id))
                    if inventory is None:
                        db.add(Inventory(branch_id=branches[branch_name].id, product_variant_id=variant.id, stock_quantity=branch_stock))


if __name__ == "__main__":
    seed_development_data()
    print("Development seed completed")

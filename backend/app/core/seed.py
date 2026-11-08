from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.models import (
    Branch,
    Category,
    City,
    Collection,
    Color,
    Inventory,
    Permission,
    Product,
    ProductImage,
    ProductSupplier,
    ProductVariant,
    Role,
    Season,
    Size,
    Subscription,
    SubscriptionPlan,
    Supplier,
    SupplierSupplyOffer,
    Tenant,
    User,
)
from app.core.security import hash_password

LEGACY_TENANT_NAME = "Empresa Legado"
DEMO_TENANT_ONE_NAME = "Boutique Aurora"
DEMO_TENANT_TWO_NAME = "Moda Boreal"

SUBSCRIPTION_PLANS_SEED = (
    ("BASIC", "Básico", Decimal("199.00"), Decimal("1990.00"), "BOB", 2, False, True),
    ("PROFESSIONAL", "Profesional", Decimal("499.00"), Decimal("4990.00"), "BOB", 10, True, True),
)

DEMO_SAAS_TENANTS_SEED = (
    {
        "name": DEMO_TENANT_ONE_NAME,
        "plan_code": "BASIC",
        "admin": ("Valeria", "Aurora", "admin@boutiqueaurora.com", "71000001", "AuroraAdmin123!"),
        "manager": ("Diego", "Aurora", "encargado@boutiqueaurora.com", "71000002", "AuroraManager123!"),
        "branches": (
            ("La Paz", "Aurora La Paz", "Av. 6 de Agosto 2450, Sopocachi", "71001001"),
            ("El Alto", "Aurora El Alto", "Av. Juan Pablo II 1180, Ciudad Satélite", "71001002"),
        ),
    },
    {
        "name": DEMO_TENANT_TWO_NAME,
        "plan_code": "PROFESSIONAL",
        "admin": ("Mateo", "Boreal", "admin@modaboreal.com", "72000001", "BorealAdmin123!"),
        "manager": ("Lucía", "Boreal", "encargado@modaboreal.com", "72000002", "BorealManager123!"),
        "branches": (
            ("Tarija", "Boreal Tarija", "Calle La Madrid 345, Zona Central", "72001001"),
            ("Yacuiba", "Boreal Yacuiba", "Av. San Martín 820", "72001002"),
        ),
    },
)

ROLES = {
    "ADMIN": "Administrador",
    "PLATFORM_ADMIN": "Administrador de Plataforma SaaS",
    "CLIENT": "Cliente",
    "BRANCH_MANAGER": "Encargado de sucursal",
    "CASHIER": "Cajero",
    "SUPPLIER": "Proveedor",
}

TENANT_PERMISSIONS = {
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

PLATFORM_PERMISSIONS = {
    "saas.tenants.manage": "Gestionar empresas SaaS",
    "saas.plans.manage": "Gestionar planes de suscripción SaaS",
    "saas.subscriptions.manage": "Gestionar suscripciones SaaS",
}

PERMISSIONS = {**TENANT_PERMISSIONS, **PLATFORM_PERMISSIONS}

ROLE_PERMISSIONS = {
    "ADMIN": set(TENANT_PERMISSIONS),
    "PLATFORM_ADMIN": set(PLATFORM_PERMISSIONS),
    "CLIENT": {"catalog.read", "catalog.availability", "reservations.read", "reservations.create", "reservations.cancel", "cart.manage", "sales.read", "payments.electronic", "recommendations.read", "virtual_fitting.use"},
    "BRANCH_MANAGER": {"catalog.read", "catalog.availability", "inventory.read", "inventory.adjust", "reservations.read", "reservations.manage", "sales.read"},
    "CASHIER": {"catalog.read", "catalog.availability", "inventory.read", "sales.read", "sales.create", "payments.cash"},
    "SUPPLIER": {"catalog.read", "suppliers.portal"},
}

PLATFORM_ADMIN_DEMO_USER = (
    "Plataforma",
    "SaaS",
    "platform.admin@fashionstore.com",
    "70009999",
    "PlatformAdmin123!",
)

DEMO_USERS = {
    "CLIENT": ("Cliente", "Demo", "client.demo@fashionstore.com", "70000001", "Client123!"),
    "BRANCH_MANAGER": ("Encargado", "Demo", "manager.demo@fashionstore.com", "70000002", "Manager123!"),
    "CASHIER": ("Cajero", "Demo", "cashier.demo@fashionstore.com", "70000003", "Cashier123!"),
    "SUPPLIER": ("Proveedor", "Demo", "supplier.demo@fashionstore.com", "70000004", "Supplier123!"),
}


def _ensure_roles_and_cities(db: Session) -> tuple[dict[str, Role], dict[str, City]]:
    roles: dict[str, Role] = {}
    for code, name in ROLES.items():
        role = db.scalar(select(Role).where(Role.code == code))
        if role is None:
            role = Role(code=code, name=name)
            db.add(role)
            db.flush()
        roles[code] = role

    cities: dict[str, City] = {}
    for city_name in ("Santa Cruz", "Cochabamba", "La Paz", "El Alto", "Tarija", "Yacuiba"):
        city = db.scalar(select(City).where(City.name == city_name))
        if city is None:
            city = City(name=city_name)
            db.add(city)
            db.flush()
        cities[city_name] = city

    return roles, cities


def _get_or_create_tenant(db: Session, name: str) -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.name == name))
    if tenant is None:
        tenant = Tenant(name=name, status="ACTIVE")
        db.add(tenant)
        db.flush()
    return tenant


def seed_saas_plans_and_demo_tenants(db: Session) -> None:
    roles, cities = _ensure_roles_and_cities(db)

    platform_permissions: list[Permission] = []
    for code, name in PLATFORM_PERMISSIONS.items():
        perm = db.scalar(select(Permission).where(Permission.code == code))
        if perm is None:
            perm = Permission(code=code, name=name)
            db.add(perm)
            db.flush()
        platform_permissions.append(perm)
    roles["PLATFORM_ADMIN"].permissions = platform_permissions

    pf_first, pf_last, pf_email, pf_phone, pf_password = PLATFORM_ADMIN_DEMO_USER
    platform_admin = db.scalar(
        select(User).where(
            User.tenant_id.is_(None),
            User.email == pf_email.lower(),
        )
    )
    if platform_admin is None:
        db.add(
            User(
                tenant_id=None,
                role=roles["PLATFORM_ADMIN"],
                first_name=pf_first,
                last_name=pf_last,
                email=pf_email.lower(),
                phone=pf_phone,
                password_hash=hash_password(pf_password),
            )
        )
        db.flush()

    plans: dict[str, SubscriptionPlan] = {}
    for code, name, price_m, price_a, curr, max_branches, gen_reports, is_active in SUBSCRIPTION_PLANS_SEED:
        plan = db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == code))
        if plan is None:
            plan = SubscriptionPlan(
                code=code,
                name=name,
                price_monthly=price_m,
                price_annual=price_a,
                currency=curr,
                max_active_branches=max_branches,
                generative_reports_enabled=gen_reports,
                is_active=is_active,
            )
            db.add(plan)
            db.flush()
        else:
            plan.name = name
            plan.price_monthly = price_m
            plan.price_annual = price_a
            plan.currency = curr
            plan.max_active_branches = max_branches
            plan.generative_reports_enabled = gen_reports
            plan.is_active = is_active
        plans[code] = plan

    # Ensure legacy tenant exists as an isolated entity for existing/legacy data
    _get_or_create_tenant(db, LEGACY_TENANT_NAME)

    for tenant_spec in DEMO_SAAS_TENANTS_SEED:
        tenant = _get_or_create_tenant(db, str(tenant_spec["name"]))
        plan = plans[str(tenant_spec["plan_code"])]

        active_sub = db.scalar(
            select(Subscription).where(
                Subscription.tenant_id == tenant.id,
                Subscription.status == "ACTIVE",
            )
        )
        if active_sub is None:
            db.add(
                Subscription(
                    tenant_id=tenant.id,
                    plan_id=plan.id,
                    status="ACTIVE",
                    valid_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    valid_until=None,
                )
            )
            db.flush()
        else:
            active_sub.plan_id = plan.id

        tenant_branches: list[Branch] = []
        for city_name, branch_name, address, phone in tenant_spec["branches"]:
            branch = db.scalar(
                select(Branch).where(
                    Branch.tenant_id == tenant.id,
                    Branch.city_id == cities[city_name].id,
                    Branch.name == branch_name,
                )
            )
            if branch is None:
                branch = Branch(
                    tenant_id=tenant.id,
                    city_id=cities[city_name].id,
                    name=branch_name,
                    address=address,
                    phone=phone,
                )
                db.add(branch)
                db.flush()
            tenant_branches.append(branch)

        admin_first, admin_last, admin_email, admin_phone, admin_password = tenant_spec["admin"]
        admin_user = db.scalar(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == admin_email.lower(),
            )
        )
        if admin_user is None:
            db.add(
                User(
                    tenant_id=tenant.id,
                    role=roles["ADMIN"],
                    first_name=admin_first,
                    last_name=admin_last,
                    email=admin_email.lower(),
                    phone=admin_phone,
                    password_hash=hash_password(admin_password),
                )
            )
            db.flush()

        mgr_first, mgr_last, mgr_email, mgr_phone, mgr_password = tenant_spec["manager"]
        mgr_user = db.scalar(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == mgr_email.lower(),
            )
        )
        if mgr_user is None:
            mgr_user = User(
                tenant_id=tenant.id,
                role=roles["BRANCH_MANAGER"],
                first_name=mgr_first,
                last_name=mgr_last,
                email=mgr_email.lower(),
                phone=mgr_phone,
                password_hash=hash_password(mgr_password),
            )
            db.add(mgr_user)
            db.flush()
        if tenant_branches and tenant_branches[0] not in mgr_user.branches:
            mgr_user.branches.append(tenant_branches[0])


def seed_development_data() -> None:
    if settings.app_env != "development":
        raise RuntimeError("El seed de desarrollo solo puede ejecutarse con APP_ENV=development")
    if not settings.seed_admin_password:
        raise RuntimeError("SEED_ADMIN_PASSWORD es obligatorio para ejecutar el seed")

    with SessionLocal.begin() as db:
        roles, cities = _ensure_roles_and_cities(db)
        legacy_tenant = _get_or_create_tenant(db, LEGACY_TENANT_NAME)

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

        admin = db.scalar(
            select(User).where(
                User.email == settings.seed_admin_email.lower(),
                (User.tenant_id == legacy_tenant.id) | (User.tenant_id.is_(None)),
            )
        )
        if admin is None:
            db.add(
                User(
                    tenant_id=legacy_tenant.id,
                    role=roles["ADMIN"],
                    first_name="Administrador",
                    last_name="FashionStore",
                    email=settings.seed_admin_email.lower(),
                    phone="000000000",
                    password_hash=hash_password(settings.seed_admin_password),
                )
            )
        elif admin.tenant_id is None:
            admin.tenant_id = legacy_tenant.id

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

        branches = {}
        branch_data = (("Santa Cruz", "FashionStore Centro", "Av. Principal 100", "70001001"), ("Cochabamba", "FashionStore Norte", "Av. América 200", "70001002"))
        for city_name, branch_name, address, phone in branch_data:
            branch = db.scalar(
                select(Branch).where(
                    Branch.city_id == cities[city_name].id,
                    Branch.name == branch_name,
                    (Branch.tenant_id == legacy_tenant.id) | (Branch.tenant_id.is_(None)),
                )
            )
            if branch is None:
                branch = Branch(tenant_id=legacy_tenant.id, city_id=cities[city_name].id, name=branch_name, address=address, phone=phone)
                db.add(branch)
                db.flush()
            elif branch.tenant_id is None:
                branch.tenant_id = legacy_tenant.id
            branches[branch_name] = branch

        supplier = db.scalar(
            select(Supplier).where(
                Supplier.tax_id == "DEMO-NIT-001",
                (Supplier.tenant_id == legacy_tenant.id) | (Supplier.tenant_id.is_(None)),
            )
        )
        if supplier is None:
            supplier = Supplier(tenant_id=legacy_tenant.id, trade_name="Textiles Andinos Demo", legal_name="Textiles Andinos S.R.L.", tax_id="DEMO-NIT-001", email="contacto@textilesandinos.com", phone="70002001", address="Parque Industrial, Santa Cruz")
            db.add(supplier)
            db.flush()
        elif supplier.tenant_id is None:
            supplier.tenant_id = legacy_tenant.id

        for role_code, (first_name, last_name, email, phone, password) in DEMO_USERS.items():
            user = db.scalar(
                select(User).where(
                    User.email == email,
                    (User.tenant_id == legacy_tenant.id) | (User.tenant_id.is_(None)),
                )
            )
            if user is None:
                user = User(tenant_id=legacy_tenant.id, role=roles[role_code], supplier=supplier if role_code == "SUPPLIER" else None, first_name=first_name, last_name=last_name, email=email, phone=phone, password_hash=hash_password(password))
                db.add(user)
                db.flush()
            elif user.tenant_id is None:
                user.tenant_id = legacy_tenant.id
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
            category = db.scalar(
                select(Category).where(
                    Category.name == category_name,
                    (Category.tenant_id == legacy_tenant.id) | (Category.tenant_id.is_(None)),
                )
            )
            if category is None:
                category = Category(tenant_id=legacy_tenant.id, name=category_name, description=description)
                db.add(category)
                db.flush()
            elif category.tenant_id is None:
                category.tenant_id = legacy_tenant.id
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
        season = db.scalar(
            select(Season).where(
                Season.name == "Demo Primavera-Verano 2026",
                (Season.tenant_id == legacy_tenant.id) | (Season.tenant_id.is_(None)),
            )
        )
        if season is None:
            season = Season(tenant_id=legacy_tenant.id, name="Demo Primavera-Verano 2026", starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31))
            db.add(season)
            db.flush()
        elif season.tenant_id is None:
            season.tenant_id = legacy_tenant.id
        collection = db.scalar(select(Collection).where(Collection.season_id == season.id, Collection.name == "Demo Esenciales"))
        if collection is None:
            collection = Collection(tenant_id=legacy_tenant.id, season_id=season.id, name="Demo Esenciales", description="Colección demo para pruebas de catálogo, reservas y ventas")
            db.add(collection)
            db.flush()
        elif collection.tenant_id is None:
            collection.tenant_id = legacy_tenant.id

        products = (("DEMO-ABR-001", "Abrigo Demo Atelier", "abrigo-demo-atelier", 450, "Demo Abrigos", "Prenda abrigada de corte recto, confeccionada para la colección de temporada."), ("DEMO-ABR-002", "Chaqueta Demo Urbana", "chaqueta-demo-urbana", 380, "Demo Abrigos", "Chaqueta ligera con acabado urbano y bolsillos funcionales."), ("DEMO-CAM-001", "Camisa Demo Oxford", "camisa-demo-oxford", 220, "Demo Camisas", "Camisa versátil de algodón para uso diario."))
        for code, name, slug, price, category_name, description in products:
            product = db.scalar(
                select(Product).where(
                    Product.code == code,
                    (Product.tenant_id == legacy_tenant.id) | (Product.tenant_id.is_(None)),
                )
            )
            if product is None:
                product = Product(tenant_id=legacy_tenant.id, category_id=categories[category_name].id, season_id=season.id, collection_id=collection.id, audience="UNISEX", size_system="ALPHA", code=code, name=name, slug=slug, description=description, price=price)
                db.add(product)
                db.flush()
            elif product.tenant_id is None:
                product.tenant_id = legacy_tenant.id
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
                    variant = ProductVariant(tenant_id=legacy_tenant.id, product_id=product.id, size_id=sizes[size_name].id, color_id=colors[color_name].id, sku=f"{code}-{size_name.split()[-1]}-{color_name.split()[-1].upper()}")
                    db.add(variant)
                    db.flush()
                elif variant.tenant_id is None:
                    variant.tenant_id = legacy_tenant.id
                offer = db.scalar(select(SupplierSupplyOffer).where(SupplierSupplyOffer.supplier_id == supplier.id, SupplierSupplyOffer.product_variant_id == variant.id))
                if offer is None:
                    db.add(SupplierSupplyOffer(tenant_id=legacy_tenant.id, supplier_id=supplier.id, product_variant_id=variant.id, season_id=season.id, collection_id=collection.id, status="AVAILABLE", available_quantity=25, expected_date=date(2026, 10, 15), notes="Oferta demo para pruebas de abastecimiento."))
                elif offer.tenant_id is None:
                    offer.tenant_id = legacy_tenant.id
                for branch_name, branch_stock in (("FashionStore Centro", stock), ("FashionStore Norte", stock + 4)):
                    inventory = db.scalar(select(Inventory).where(Inventory.branch_id == branches[branch_name].id, Inventory.product_variant_id == variant.id))
                    if inventory is None:
                        db.add(Inventory(tenant_id=legacy_tenant.id, branch_id=branches[branch_name].id, product_variant_id=variant.id, stock_quantity=branch_stock))
                    elif inventory.tenant_id is None:
                        inventory.tenant_id = legacy_tenant.id

        seed_saas_plans_and_demo_tenants(db)


if __name__ == "__main__":
    seed_development_data()
    print("Development seed completed")

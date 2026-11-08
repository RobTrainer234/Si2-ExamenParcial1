from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import (
    AIRecommendation,
    Base,
    Bitacora,
    Branch,
    Cart,
    Category,
    Collection,
    Inventory,
    InventoryMovement,
    Payment,
    Product,
    ProductVariant,
    Promotion,
    Reservation,
    Sale,
    Season,
    Subscription,
    SubscriptionPlan,
    Supplier,
    SupplierSupplyOffer,
    Tenant,
    User,
    VirtualFittingSession,
)
from app.modules.subscriptions import service as subscription_service


def test_pause_blocks_subscription_access_and_mutations_without_suspending_tenant():
    from fastapi import HTTPException
    from datetime import timedelta

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(name="Paused Tenant", status="ACTIVE")
        plan = SubscriptionPlan(code="BASIC", name="Basic", max_active_branches=2)
        now = datetime.now(timezone.utc)
        sub = Subscription(
            tenant=tenant,
            plan=plan,
            status="PAUSED",
            valid_from=now - timedelta(days=2),
            valid_until=now + timedelta(days=20),
            paused_at=now,
        )
        session.add_all([tenant, plan, sub])
        session.flush()

        assert tenant.status == "ACTIVE"
        assert subscription_service.check_tenant_feature(session, tenant.id, "generative_reports_enabled") is False
        assert subscription_service.is_tenant_subscription_expired(session, tenant.id) is True

        with pytest.raises(HTTPException) as renew_error:
            subscription_service.renew_subscription(session, tenant.id, renewed_at=now)
        with pytest.raises(HTTPException) as pause_error:
            subscription_service.pause_subscription(session, tenant.id, paused_at=now)
        assert renew_error.value.detail["code"] == "SUBSCRIPTION_PAUSED"
        assert pause_error.value.detail["code"] == "SUBSCRIPTION_ALREADY_PAUSED"
        assert tenant.status == "ACTIVE"


def test_pause_blocks_downgrade_from_leaving_paused_constraint_state():
    from pathlib import Path

    migration = (Path(__file__).resolve().parents[1] / "migrations" / "versions" / "s1o3m5q7u9w1_cu03_subscription_pause.py").read_text()

    assert "UPDATE subscriptions SET status = 'SUSPENDED' WHERE status = 'PAUSED'" in migration
    assert "batch_op.drop_constraint(\"ck_subscriptions_status_valid\", type_=\"check\")" in migration
    assert "status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED')" in migration
    assert "batch_op.drop_column(\"paused_at\")" in migration


def test_renewal_30_days_extends_valid_subscription_and_records_audit():
    from datetime import timedelta
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(name="Renewal Tenant")
        plan = SubscriptionPlan(code="BASIC", name="Basic", max_active_branches=2)
        now = datetime.now(timezone.utc)
        sub = Subscription(tenant=tenant, plan=plan, status="ACTIVE", valid_from=now - timedelta(days=5), valid_until=now + timedelta(days=10))
        session.add_all([tenant, plan, sub])
        session.flush()
        result = subscription_service.renew_subscription(session, tenant.id, renewed_at=now)
        assert result.valid_until == now + timedelta(days=40)
        assert session.query(Bitacora).filter_by(action="SUBSCRIPTION_RENEWED").one().new_values["plan_code"] == "BASIC"


def test_pause_freezes_finite_validity_and_resume_restores_elapsed_time():
    from datetime import timedelta
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(name="Pause Tenant")
        plan = SubscriptionPlan(code="BASIC", name="Basic", max_active_branches=2)
        now = datetime.now(timezone.utc)
        sub = Subscription(tenant=tenant, plan=plan, status="ACTIVE", valid_from=now - timedelta(days=2), valid_until=now + timedelta(days=20))
        session.add_all([tenant, plan, sub])
        session.flush()
        paused = subscription_service.pause_subscription(session, tenant.id, paused_at=now)
        assert paused.status == "PAUSED" and paused.paused_at == now
        assert subscription_service._evaluate_subscription_window(paused, now=now)["days_remaining"] == 20
        resumed = subscription_service.resume_subscription(session, tenant.id, resumed_at=now + timedelta(days=3))
        assert resumed.status == "ACTIVE"
        assert resumed.valid_until == now + timedelta(days=23)


def test_pause_indefinite_and_expired_states_are_deliberate():
    from datetime import timedelta
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(name="State Tenant")
        plan = SubscriptionPlan(code="BASIC", name="Basic", max_active_branches=2)
        session.add_all([tenant, plan])
        session.flush()
        indefinite = Subscription(tenant=tenant, plan=plan, status="ACTIVE", valid_from=datetime(2025, 1, 1), valid_until=None)
        session.add(indefinite)
        session.flush()
        paused = subscription_service.pause_subscription(session, tenant.id, paused_at=datetime(2025, 1, 2))
        assert paused.valid_until is None
        assert subscription_service.resume_subscription(session, tenant.id, resumed_at=datetime(2025, 1, 5)).valid_until is None


def test_expired_renewal_starts_now_and_already_paused_is_rejected():
    from datetime import timedelta
    from fastapi import HTTPException
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(name="Expired Tenant")
        plan = SubscriptionPlan(code="BASIC", name="Basic", max_active_branches=2)
        now = datetime.now(timezone.utc)
        sub = Subscription(tenant=tenant, plan=plan, status="EXPIRED", valid_from=now - timedelta(days=40), valid_until=now - timedelta(days=10))
        session.add_all([tenant, plan, sub])
        session.flush()
        renewed = subscription_service.renew_subscription(session, tenant.id, renewed_at=now)
        assert renewed.valid_until == now + timedelta(days=30)
        subscription_service.pause_subscription(session, tenant.id, paused_at=now)
        with pytest.raises(HTTPException) as error:
            subscription_service.pause_subscription(session, tenant.id, paused_at=now)
        assert error.value.detail["code"] == "SUBSCRIPTION_ALREADY_PAUSED"


def test_plan_entitlements_and_subscription_history_round_trip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = Tenant(name="Acme", status="ACTIVE")
        basic = SubscriptionPlan(
            code="BASIC", name="Basic", max_active_branches=2, generative_reports_enabled=False
        )
        professional = SubscriptionPlan(
            code="PROFESSIONAL", name="Professional", max_active_branches=10,
            generative_reports_enabled=True,
        )
        tenant.subscriptions.extend([
            Subscription(plan=basic, status="CANCELLED", valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc), valid_until=datetime(2025, 2, 1, tzinfo=timezone.utc)),
            Subscription(plan=professional, status="ACTIVE", valid_from=datetime(2025, 2, 1, tzinfo=timezone.utc)),
        ])
        session.add(tenant)
        session.commit()
        session.expire_all()

        stored_tenant = session.query(Tenant).filter_by(name="Acme").one()
        history = sorted(stored_tenant.subscriptions, key=lambda item: item.valid_from)
        assert [(item.plan.code, item.status) for item in history] == [
            ("BASIC", "CANCELLED"), ("PROFESSIONAL", "ACTIVE")
        ]
        assert (history[0].plan.max_active_branches, history[0].plan.generative_reports_enabled) == (2, False)
        assert (history[1].plan.max_active_branches, history[1].plan.generative_reports_enabled) == (10, True)
        assert history[0].valid_until == datetime(2025, 2, 1)
        assert history[1].valid_until is None


def test_tenant_generates_created_and_updated_timestamps():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = Tenant(name="Acme")
        session.add(tenant)
        session.commit()

        assert tenant.created_at is not None
        assert tenant.updated_at is not None
        assert tenant.created_at == tenant.updated_at


def test_tenants_can_share_display_name():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all([Tenant(name="Acme"), Tenant(name="Acme")])
        session.commit()

        assert session.query(Tenant).filter_by(name="Acme").count() == 2


def test_subscription_rejects_invalid_status_and_interval():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(name="Acme")
        plan = SubscriptionPlan(code="BASIC", name="Basic", max_active_branches=2)
        session.add_all([tenant, plan])
        session.flush()
        session.add(Subscription(
            tenant=tenant, plan=plan, status="UNKNOWN",
            valid_from=datetime(2025, 2, 1), valid_until=datetime(2025, 1, 1),
        ))
        with pytest.raises(IntegrityError):
            session.commit()


TENANT_OWNED_MODELS = [
    User,
    Branch,
    Category,
    Supplier,
    Season,
    Promotion,
    Collection,
    Product,
    ProductVariant,
    Inventory,
    Reservation,
    Cart,
    Sale,
    Payment,
    InventoryMovement,
    SupplierSupplyOffer,
    VirtualFittingSession,
    AIRecommendation,
    Bitacora,
]


def test_tenant_id_present_and_nullable_on_tenant_owned_entities():
    for model in TENANT_OWNED_MODELS:
        table = model.__table__
        assert "tenant_id" in table.columns, f"{model.__name__} missing tenant_id column in table {table.name}"
        col = table.columns["tenant_id"]
        assert col.nullable is True, f"{model.__name__}.tenant_id should be nullable"
        fks = list(col.foreign_keys)
        assert len(fks) == 1, f"{model.__name__}.tenant_id should have a foreign key to tenants.id"
        assert fks[0].target_fullname == "tenants.id", f"{model.__name__}.tenant_id FK targets {fks[0].target_fullname}"
        assert hasattr(model, "tenant"), f"{model.__name__} missing 'tenant' relationship attribute"


def test_tenant_relationships_bidirectional_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = Tenant(name="Empresa Moda 1", status="ACTIVE")
        session.add(tenant)
        session.flush()

        from app.core.models import City, Color, Role, Size

        role = Role(code="TEST_ROLE", name="Test Role")
        city = City(name="Santa Cruz")
        size = Size(name="M")
        color = Color(name="Azul")
        session.add_all([role, city, size, color])
        session.flush()

        user = User(
            tenant=tenant,
            role=role,
            first_name="Juan",
            last_name="Perez",
            email="juan@empresa1.com",
            phone="70000001",
            password_hash="hash",
        )
        branch = Branch(tenant=tenant, city=city, name="Sucursal Norte", address="Calle 1", phone="70000002")
        category = Category(tenant=tenant, name="Camisas")
        supplier = Supplier(tenant=tenant, trade_name="Proveedor 1")
        season = Season(tenant=tenant, name="Verano 2026")
        session.add_all([user, branch, category, supplier, season])
        session.flush()

        collection = Collection(tenant=tenant, season=season, name="Coleccion Lino")
        product = Product(
            tenant=tenant,
            category=category,
            season=season,
            collection=collection,
            code="CAM-001",
            name="Camisa Lino",
            slug="camisa-lino",
            price=150,
        )
        session.add_all([collection, product])
        session.flush()

        variant = ProductVariant(tenant=tenant, product=product, size=size, color=color, sku="CAM-001-M-AZUL")
        session.add(variant)
        session.flush()

        inventory = Inventory(tenant=tenant, branch=branch, product_variant=variant, stock_quantity=10)
        cart = Cart(tenant=tenant, customer=user)
        reservation = Reservation(tenant=tenant, customer=user, branch=branch, status="PENDING")
        sale = Sale(tenant=tenant, order_number="ORD-001", customer_id=user.id, branch_id=branch.id, channel="WEB", subtotal=150, total=150)
        session.add_all([inventory, cart, reservation, sale])
        session.flush()

        payment = Payment(tenant=tenant, sale=sale, method="QR", amount=150)
        movement = InventoryMovement(tenant=tenant, inventory=inventory, movement_type="IN", quantity=10, stock_before=0, stock_after=10)
        promotion = Promotion(tenant=tenant, name="Descuento 10%", discount_type="PERCENTAGE", discount_value=10, starts_at=datetime.now(timezone.utc), ends_at=datetime.now(timezone.utc))
        offer = SupplierSupplyOffer(tenant=tenant, supplier=supplier, product_variant=variant, season=season, available_quantity=50)
        session.add_all([payment, movement, promotion, offer])
        session.flush()

        bitacora = Bitacora(tenant=tenant, user=user, action="CREATE", entity_type="Product", entity_id=product.id)
        vton = VirtualFittingSession(tenant=tenant, customer_id=user.id, product_id=product.id)
        recom = AIRecommendation(tenant=tenant, customer_id=user.id, product_id=product.id, source="trending")
        session.add_all([bitacora, vton, recom])
        session.commit()
        session.expire_all()

        loaded_tenant = session.query(Tenant).filter_by(id=tenant.id).one()
        assert user in loaded_tenant.users
        assert branch in loaded_tenant.branches
        assert category in loaded_tenant.categories
        assert supplier in loaded_tenant.suppliers
        assert season in loaded_tenant.seasons
        assert collection in loaded_tenant.collections
        assert product in loaded_tenant.products
        assert variant in loaded_tenant.product_variants
        assert inventory in loaded_tenant.inventories
        assert reservation in loaded_tenant.reservations
        assert cart in loaded_tenant.carts
        assert sale in loaded_tenant.sales
        assert payment in loaded_tenant.payments
        assert movement in loaded_tenant.inventory_movements
        assert promotion in loaded_tenant.promotions
        assert offer in loaded_tenant.supply_offers
        assert bitacora in loaded_tenant.bitacoras
        assert vton in loaded_tenant.virtual_fitting_sessions
        assert recom in loaded_tenant.ai_recommendations

        assert loaded_tenant.users[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.branches[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.categories[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.products[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.product_variants[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.inventories[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.sales[0].tenant_id == loaded_tenant.id
        assert loaded_tenant.reservations[0].tenant_id == loaded_tenant.id


def test_legacy_records_persist_with_null_tenant_id():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        from app.core.models import City, Role

        role = Role(code="LEGACY_ROLE", name="Legacy Role")
        city = City(name="Cochabamba")
        session.add_all([role, city])
        session.flush()

        user = User(
            role=role,
            first_name="Carlos",
            last_name="Legado",
            email="carlos@legacy.com",
            phone="70000003",
            password_hash="hash",
            tenant_id=None,
        )
        branch = Branch(city=city, name="Sucursal Legada", address="Calle Vieja", phone="70000004", tenant_id=None)
        category = Category(name="Categoria Legada", tenant_id=None)
        bitacora = Bitacora(action="PLATFORM_INIT", entity_type="System", tenant_id=None)
        session.add_all([user, branch, category, bitacora])
        session.commit()

        assert user.tenant_id is None
        assert user.tenant is None
        assert branch.tenant_id is None
        assert category.tenant_id is None
        assert bitacora.tenant_id is None


def _unique_constraint_column_sets(model) -> set[tuple[str, ...]]:
    from sqlalchemy import UniqueConstraint

    return {
        tuple(col.name for col in constraint.columns)
        for constraint in model.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def _index_column_sets(model) -> set[tuple[str, ...]]:
    return {tuple(col.name for col in index.columns) for index in model.__table__.indexes}


def test_tenant_scoped_unique_constraints_and_indexes_metadata():
    from app.core.models import City, Color, Permission, RefreshToken, Role, Size

    # Global catalogs must keep global single-column uniqueness
    assert Role.__table__.c.code.unique is True
    assert Permission.__table__.c.code.unique is True
    assert City.__table__.c.name.unique is True
    assert Size.__table__.c.name.unique is True
    assert Color.__table__.c.name.unique is True
    assert RefreshToken.__table__.c.session_id.unique is True
    assert RefreshToken.__table__.c.token_hash.unique is True

    # Tenant-owned entities must NOT enforce global single-column uniqueness on tenant-scoped keys
    assert not User.__table__.c.email.unique
    assert not Category.__table__.c.name.unique
    assert not Supplier.__table__.c.tax_id.unique
    assert not Season.__table__.c.name.unique
    assert not Product.__table__.c.code.unique
    assert not Product.__table__.c.slug.unique
    assert not ProductVariant.__table__.c.sku.unique
    assert not Cart.__table__.c.customer_id.unique
    assert not Sale.__table__.c.order_number.unique
    assert not Payment.__table__.c.idempotency_key.unique

    # Composite tenant-scoped unique constraints
    assert ("tenant_id", "email") in _unique_constraint_column_sets(User)
    assert ("tenant_id", "city_id", "name") in _unique_constraint_column_sets(Branch)
    assert ("city_id", "name") not in _unique_constraint_column_sets(Branch)
    assert ("tenant_id", "name") in _unique_constraint_column_sets(Category)
    assert ("tenant_id", "tax_id") in _unique_constraint_column_sets(Supplier)
    assert ("tenant_id", "name") in _unique_constraint_column_sets(Season)
    assert ("season_id", "name") in _unique_constraint_column_sets(Collection)
    assert ("tenant_id", "code") in _unique_constraint_column_sets(Product)
    assert ("tenant_id", "slug") in _unique_constraint_column_sets(Product)
    assert ("tenant_id", "sku") in _unique_constraint_column_sets(ProductVariant)
    assert ("product_id", "size_id", "color_id") in _unique_constraint_column_sets(ProductVariant)
    assert ("branch_id", "product_variant_id") in _unique_constraint_column_sets(Inventory)
    assert ("tenant_id", "customer_id") in _unique_constraint_column_sets(Cart)
    assert ("tenant_id", "order_number") in _unique_constraint_column_sets(Sale)
    assert ("tenant_id", "provider", "transaction_reference") in _unique_constraint_column_sets(Payment)
    assert ("provider", "transaction_reference") not in _unique_constraint_column_sets(Payment)
    assert ("tenant_id", "idempotency_key") in _unique_constraint_column_sets(Payment)

    # Tenant-aware composite indexes for common queries/audit
    assert ("tenant_id", "name") in _index_column_sets(Product)
    assert ("tenant_id", "branch_id") in _index_column_sets(Inventory)
    assert ("tenant_id", "branch_id", "status") in _index_column_sets(Reservation)
    assert ("tenant_id", "created_at") in _index_column_sets(Sale)
    assert ("tenant_id", "fecha_creacion") in _index_column_sets(Bitacora)
    assert ("tenant_id", "tipo_entidad", "entidad_id") in _index_column_sets(Bitacora)


def test_two_tenants_can_share_business_keys_without_collision():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        from app.core.models import City, Color, Role, Size

        role = Role(code="ADMIN", name="Admin")
        city = City(name="La Paz")
        size = Size(name="M")
        color = Color(name="Negro")
        tenant_a = Tenant(name="Boutique Alpha", status="ACTIVE")
        tenant_b = Tenant(name="Boutique Beta", status="ACTIVE")
        session.add_all([role, city, size, color, tenant_a, tenant_b])
        session.flush()

        for tenant in (tenant_a, tenant_b):
            user = User(
                tenant=tenant,
                role=role,
                first_name="Admin",
                last_name=tenant.name,
                email="admin@boutique.com",
                phone="70000100",
                password_hash="hash",
            )
            branch = Branch(tenant=tenant, city=city, name="Sucursal Central", address="Av. 1", phone="70000101")
            category = Category(tenant=tenant, name="Camisas")
            supplier = Supplier(tenant=tenant, trade_name="Textil Sur", tax_id="NIT-777")
            season = Season(tenant=tenant, name="Invierno 2026")
            session.add_all([user, branch, category, supplier, season])
            session.flush()

            product = Product(
                tenant=tenant,
                category=category,
                season=season,
                code="CAM-100",
                name="Camisa Oxford",
                slug="camisa-oxford",
                price=180,
            )
            session.add(product)
            session.flush()

            variant = ProductVariant(
                tenant=tenant,
                product=product,
                size=size,
                color=color,
                sku="CAM-100-M-NEGRO",
            )
            sale = Sale(
                tenant=tenant,
                order_number="ORD-0001",
                customer_id=user.id,
                branch_id=branch.id,
                channel="WEB",
                subtotal=180,
                total=180,
            )
            session.add_all([variant, sale])
            session.flush()

            payment = Payment(
                tenant=tenant,
                sale=sale,
                method="QR",
                provider="QR_SIMPLE",
                transaction_reference="QR-REF-001",
                idempotency_key="IDEMP-KEY-001",
                amount=180,
            )
            session.add(payment)

        session.commit()
        assert session.query(Product).filter_by(code="CAM-100").count() == 2
        assert session.query(ProductVariant).filter_by(sku="CAM-100-M-NEGRO").count() == 2
        assert session.query(Branch).filter_by(name="Sucursal Central").count() == 2
        assert session.query(User).filter_by(email="admin@boutique.com").count() == 2


def test_same_tenant_rejects_duplicate_business_keys():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        from app.core.models import City, Color, Role, Size

        role = Role(code="ADMIN", name="Admin")
        city = City(name="Santa Cruz")
        size_m = Size(name="M")
        size_l = Size(name="L")
        color = Color(name="Blanco")
        tenant = Tenant(name="Empresa Unica", status="ACTIVE")
        session.add_all([role, city, size_m, size_l, color, tenant])
        session.flush()

        user1 = User(tenant=tenant, role=role, first_name="A", last_name="B", email="dup@empresa.com", phone="70000201", password_hash="h")
        branch1 = Branch(tenant=tenant, city=city, name="Sucursal Norte", address="Dir 1", phone="70000202")
        category1 = Category(tenant=tenant, name="Pantalones")
        supplier1 = Supplier(tenant=tenant, trade_name="Prov 1", tax_id="NIT-DUP")
        season1 = Season(tenant=tenant, name="Primavera 2026")
        session.add_all([user1, branch1, category1, supplier1, season1])
        session.flush()

        product1 = Product(tenant=tenant, category=category1, code="PAN-001", name="Pantalon 1", slug="pantalon-1", price=200)
        session.add(product1)
        session.flush()

        variant1 = ProductVariant(tenant=tenant, product=product1, size=size_m, color=color, sku="PAN-001-M-BLANCO")
        cart1 = Cart(tenant=tenant, customer=user1)
        sale1 = Sale(tenant=tenant, order_number="ORD-DUP", customer_id=user1.id, branch_id=branch1.id, channel="POS", subtotal=200, total=200)
        session.add_all([variant1, cart1, sale1])
        session.flush()

        payment1 = Payment(tenant=tenant, sale=sale1, method="QR", provider="QR_SIMPLE", transaction_reference="TX-DUP", idempotency_key="IDEMP-DUP", amount=200)
        session.add(payment1)
        session.commit()

        duplicate_factories = [
            lambda: User(tenant=tenant, role=role, first_name="C", last_name="D", email="dup@empresa.com", phone="70000203", password_hash="h"),
            lambda: Branch(tenant=tenant, city=city, name="Sucursal Norte", address="Dir 2", phone="70000204"),
            lambda: Category(tenant=tenant, name="Pantalones"),
            lambda: Supplier(tenant=tenant, trade_name="Prov 2", tax_id="NIT-DUP"),
            lambda: Season(tenant=tenant, name="Primavera 2026"),
            lambda: Product(tenant=tenant, category=category1, code="PAN-001", name="Otro", slug="otro-slug", price=210),
            lambda: Product(tenant=tenant, category=category1, code="PAN-002", name="Otro", slug="pantalon-1", price=210),
            lambda: ProductVariant(tenant=tenant, product=product1, size=size_l, color=color, sku="PAN-001-M-BLANCO"),
            lambda: Cart(tenant=tenant, customer=user1),
            lambda: Sale(tenant=tenant, order_number="ORD-DUP", customer_id=user1.id, branch_id=branch1.id, channel="POS", subtotal=100, total=100),
            lambda: Payment(tenant=tenant, sale=sale1, method="QR", provider="QR_SIMPLE", transaction_reference="TX-DUP", idempotency_key="IDEMP-OTHER", amount=200),
            lambda: Payment(tenant=tenant, sale=sale1, method="QR", provider="QR_SIMPLE", transaction_reference="TX-OTHER", idempotency_key="IDEMP-DUP", amount=200),
        ]

        for make_duplicate in duplicate_factories:
            with session.begin_nested():
                session.add(make_duplicate())
                with pytest.raises(IntegrityError):
                    session.flush()


def _create_pre_t1_1_6_schema(engine) -> None:
    """Builds a disposable pre-T1.1.6 (revision o6k9l2m4n6p8) schema without SaaS tables or tenant_id columns."""
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "CREATE TABLE roles (id INTEGER PRIMARY KEY, code VARCHAR(32) NOT NULL UNIQUE, name VARCHAR(80) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE ciudades (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE, is_active BOOLEAN NOT NULL DEFAULT 1)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE tallas (id INTEGER PRIMARY KEY, name VARCHAR(20) NOT NULL UNIQUE, size_type VARCHAR(20) NOT NULL DEFAULT 'ALPHA', sort_order INTEGER NOT NULL DEFAULT 100, is_active BOOLEAN NOT NULL DEFAULT 1)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE colores (id INTEGER PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE, hex_code VARCHAR(7), is_active BOOLEAN NOT NULL DEFAULT 1)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE proveedores (id INTEGER PRIMARY KEY, trade_name VARCHAR(150) NOT NULL, legal_name VARCHAR(200), tax_id VARCHAR(50), email VARCHAR(255), phone VARCHAR(30), address VARCHAR(255), is_active BOOLEAN NOT NULL DEFAULT 1, CONSTRAINT uq_suppliers_tax_id UNIQUE (tax_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, role_id INTEGER NOT NULL REFERENCES roles(id), supplier_id INTEGER UNIQUE REFERENCES proveedores(id), first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL, email VARCHAR(255) NOT NULL, phone VARCHAR(30) NOT NULL, password_hash VARCHAR(255) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, CONSTRAINT uq_users_email UNIQUE (email))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE sucursales (id INTEGER PRIMARY KEY, city_id INTEGER NOT NULL REFERENCES ciudades(id), name VARCHAR(120) NOT NULL, address VARCHAR(255) NOT NULL, phone VARCHAR(30) NOT NULL, latitude NUMERIC(9, 6), longitude NUMERIC(9, 6), is_active BOOLEAN NOT NULL DEFAULT 1, CONSTRAINT uq_branches_city_name UNIQUE (city_id, name))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE usuario_sucursales (user_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE, branch_id INTEGER NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE, PRIMARY KEY (user_id, branch_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE categorias (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, description VARCHAR(255), is_active BOOLEAN NOT NULL DEFAULT 1, CONSTRAINT uq_categories_name UNIQUE (name))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE temporadas (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, starts_on DATE, ends_on DATE, is_active BOOLEAN NOT NULL DEFAULT 1, CONSTRAINT seasons_name_key UNIQUE (name))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE colecciones (id INTEGER PRIMARY KEY, season_id INTEGER NOT NULL REFERENCES temporadas(id), name VARCHAR(120) NOT NULL, description TEXT, is_active BOOLEAN NOT NULL DEFAULT 1, CONSTRAINT uq_collections_season_name UNIQUE (season_id, name))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE productos (id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL REFERENCES categorias(id), season_id INTEGER REFERENCES temporadas(id), collection_id INTEGER REFERENCES colecciones(id), audience VARCHAR(30) NOT NULL DEFAULT 'UNISEX', size_system VARCHAR(20) NOT NULL DEFAULT 'ALPHA', code VARCHAR(50) NOT NULL, name VARCHAR(180) NOT NULL, slug VARCHAR(200) NOT NULL, description TEXT, price NUMERIC(12, 2) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, CONSTRAINT uq_products_code UNIQUE (code), CONSTRAINT uq_products_slug UNIQUE (slug))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE producto_proveedores (product_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE, supplier_id INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE RESTRICT, PRIMARY KEY (product_id, supplier_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE variantes_producto (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES productos(id), size_id INTEGER NOT NULL REFERENCES tallas(id), color_id INTEGER NOT NULL REFERENCES colores(id), sku VARCHAR(80) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, CONSTRAINT uq_product_variants_sku UNIQUE (sku), CONSTRAINT uq_product_variants_attributes UNIQUE (product_id, size_id, color_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE ofertas_abastecimiento (id INTEGER PRIMARY KEY, supplier_id INTEGER NOT NULL REFERENCES proveedores(id), product_variant_id INTEGER NOT NULL REFERENCES variantes_producto(id), season_id INTEGER NOT NULL REFERENCES temporadas(id), collection_id INTEGER REFERENCES colecciones(id), status VARCHAR(30) NOT NULL DEFAULT 'AVAILABLE', available_quantity INTEGER NOT NULL DEFAULT 1, expected_date DATE, notes VARCHAR(255), is_active BOOLEAN NOT NULL DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE inventario (id INTEGER PRIMARY KEY, branch_id INTEGER NOT NULL REFERENCES sucursales(id), product_variant_id INTEGER NOT NULL REFERENCES variantes_producto(id), stock_quantity INTEGER NOT NULL DEFAULT 0, reserved_quantity INTEGER NOT NULL DEFAULT 0, CONSTRAINT uq_inventory_branch_variant UNIQUE (branch_id, product_variant_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE reservas (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES usuarios(id), branch_id INTEGER NOT NULL REFERENCES sucursales(id), scheduled_for DATETIME, status VARCHAR(30) NOT NULL DEFAULT 'PENDING', notes TEXT, expires_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE carritos (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES usuarios(id), status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, CONSTRAINT carts_customer_id_key UNIQUE (customer_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE ventas (id INTEGER PRIMARY KEY, order_number VARCHAR(30) NOT NULL, customer_id INTEGER REFERENCES usuarios(id), branch_id INTEGER REFERENCES sucursales(id), cashier_id INTEGER REFERENCES usuarios(id), reservation_id INTEGER REFERENCES reservas(id), channel VARCHAR(20) NOT NULL, fulfillment_type VARCHAR(20) NOT NULL DEFAULT 'PICKUP', status VARCHAR(20) NOT NULL DEFAULT 'PAID', subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0, discount NUMERIC(12, 2) NOT NULL DEFAULT 0, total NUMERIC(12, 2) NOT NULL DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
        conn.exec_driver_sql("CREATE UNIQUE INDEX ix_ventas_order_number ON ventas (order_number)")
        conn.exec_driver_sql(
            "CREATE TABLE pagos (id INTEGER PRIMARY KEY, sale_id INTEGER NOT NULL REFERENCES ventas(id), method VARCHAR(30) NOT NULL, provider VARCHAR(50), transaction_reference VARCHAR(150), idempotency_key VARCHAR(100), status VARCHAR(20) NOT NULL DEFAULT 'PENDING', amount NUMERIC(12, 2) NOT NULL DEFAULT 0, received_amount NUMERIC(12, 2), change_amount NUMERIC(12, 2) NOT NULL DEFAULT 0, metadata_json JSON, paid_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, CONSTRAINT uq_payment_provider_reference UNIQUE (provider, transaction_reference))"
        )
        conn.exec_driver_sql("CREATE UNIQUE INDEX ix_pagos_idempotency_key ON pagos (idempotency_key)")
        conn.exec_driver_sql(
            "CREATE TABLE movimientos_inventario (id INTEGER PRIMARY KEY, inventory_id INTEGER NOT NULL REFERENCES inventario(id), movement_type VARCHAR(30) NOT NULL, quantity INTEGER NOT NULL, stock_before INTEGER NOT NULL, stock_after INTEGER NOT NULL, reason VARCHAR(255), created_by INTEGER REFERENCES usuarios(id), created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE promociones (id INTEGER PRIMARY KEY, name VARCHAR(150) NOT NULL, description TEXT, discount_type VARCHAR(20) NOT NULL, discount_value NUMERIC(12, 2) NOT NULL, starts_at DATETIME NOT NULL, ends_at DATETIME NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE productos_promocion (promotion_id INTEGER NOT NULL REFERENCES promociones(id) ON DELETE CASCADE, product_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE, PRIMARY KEY (promotion_id, product_id))"
        )
        conn.exec_driver_sql(
            "CREATE TABLE sesiones_vestidor_virtual (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES usuarios(id), product_id INTEGER NOT NULL REFERENCES productos(id), status VARCHAR(20) NOT NULL DEFAULT 'STARTED', device_info VARCHAR(255), started_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, ended_at DATETIME)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE recomendaciones_ia (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES usuarios(id), product_id INTEGER NOT NULL REFERENCES productos(id), source VARCHAR(50) NOT NULL, reason TEXT, score NUMERIC(5, 4), context JSON, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, expires_at DATETIME)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE bitacora (id INTEGER PRIMARY KEY, usuario_id INTEGER REFERENCES usuarios(id), accion VARCHAR(30) NOT NULL, tipo_entidad VARCHAR(100) NOT NULL, entidad_id INTEGER, descripcion TEXT, valores_anteriores JSON, valores_nuevos JSON, direccion_ip VARCHAR(45), agente_usuario VARCHAR(500), fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )


def test_t1_1_6_additive_alembic_migration_exists_and_revises_previous_head():
    from pathlib import Path
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config()
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    rev = script_dir.get_revision("p7l0m3n5q7r9")
    assert rev is not None, "Expected revision p7l0m3n5q7r9 for T1.1.6 additive SaaS migration"
    assert rev.down_revision == "o6k9l2m4n6p8"
    assert "p7l0m3n5q7r9" in {r.revision for r in script_dir.walk_revisions()}


def test_t1_1_6_additive_migration_upgrade_and_downgrade_on_disposable_db(monkeypatch):
    import importlib
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import inspect, text

    migration_mod = importlib.import_module(
        "backend.migrations.versions.p7l0m3n5q7r9_agregar_fundacion_saas_aditiva"
    )

    engine = create_engine("sqlite:///:memory:")
    _create_pre_t1_1_6_schema(engine)

    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO roles (id, code, name, is_active) VALUES (1, 'ADMIN', 'Admin', 1)")
        conn.exec_driver_sql("INSERT INTO ciudades (id, name, is_active) VALUES (1, 'Santa Cruz', 1)")
        conn.exec_driver_sql(
            "INSERT INTO usuarios (id, role_id, first_name, last_name, email, phone, password_hash, is_active) "
            "VALUES (1, 1, 'Legacy', 'Admin', 'legacy@fashionstore.local', '70000000', 'hash', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO sucursales (id, city_id, name, address, phone, is_active) "
            "VALUES (1, 1, 'Sucursal Central', 'Av. Principal 100', '70000001', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO categorias (id, name, description, is_active) VALUES (1, 'Camisas', 'Cat', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO productos (id, category_id, code, name, slug, price, is_active) "
            "VALUES (1, 1, 'CAM-001', 'Camisa Clasica', 'camisa-clasica', 150.00, 1)"
        )

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(migration_mod, "op", op_proxy)
        migration_mod.upgrade()

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert {"tenants", "subscription_plans", "subscriptions"}.issubset(table_names)

    for model in TENANT_OWNED_MODELS:
        tname = model.__table__.name
        cols = {c["name"]: c for c in inspector.get_columns(tname)}
        assert "tenant_id" in cols, f"Table {tname} missing tenant_id after T1.1.6 upgrade"
        assert cols["tenant_id"]["nullable"] is True, f"Table {tname}.tenant_id must remain nullable in T1.1.6"

        fks = [fk for fk in inspector.get_foreign_keys(tname) if fk["constrained_columns"] == ["tenant_id"]]
        assert len(fks) == 1, f"Table {tname} missing FK on tenant_id to tenants.id"
        assert fks[0]["referred_table"] == "tenants"
        expected_ondelete = "SET NULL" if tname == "bitacora" else "CASCADE"
        assert fks[0].get("options", {}).get("ondelete") == expected_ondelete

        index_names = {idx["name"] for idx in inspector.get_indexes(tname)}
        assert f"ix_{tname}_tenant_id" in index_names, f"Table {tname} missing index ix_{tname}_tenant_id"

    with engine.connect() as conn:
        tenants = conn.execute(text("SELECT id, name, status FROM tenants")).fetchall()
        assert len(tenants) == 1
        assert tenants[0][1] == migration_mod.LEGACY_TENANT_NAME
        assert tenants[0][2] == "ACTIVE"

        legacy_user = conn.execute(text("SELECT email, tenant_id FROM usuarios WHERE id = 1")).fetchone()
        assert legacy_user == ("legacy@fashionstore.local", None)

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(migration_mod, "op", op_proxy)
        migration_mod.downgrade()

    inspector_after = inspect(engine)
    remaining_tables = set(inspector_after.get_table_names())
    assert {"tenants", "subscription_plans", "subscriptions"}.isdisjoint(remaining_tables)
    for model in TENANT_OWNED_MODELS:
        tname = model.__table__.name
        cols = {c["name"] for c in inspector_after.get_columns(tname)}
        assert "tenant_id" not in cols, f"Table {tname} still has tenant_id after downgrade"

    with engine.connect() as conn:
        assert conn.execute(text("SELECT email FROM usuarios WHERE id = 1")).scalar_one() == "legacy@fashionstore.local"


def test_t1_1_6_migration_generates_additive_postgresql_ddl(monkeypatch):
    import importlib
    from io import StringIO
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy.dialects import postgresql

    migration_mod = importlib.import_module(
        "backend.migrations.versions.p7l0m3n5q7r9_agregar_fundacion_saas_aditiva"
    )

    buf = StringIO()
    ctx = MigrationContext.configure(
        dialect=postgresql.dialect(),
        opts={"as_sql": True, "output_buffer": buf},
    )
    op_proxy = Operations(ctx)
    monkeypatch.setattr(migration_mod, "op", op_proxy)
    migration_mod.upgrade()

    sql = buf.getvalue()
    assert "CREATE TABLE tenants" in sql
    assert "CREATE TABLE subscription_plans" in sql
    assert "CREATE TABLE subscriptions" in sql
    assert "ADD COLUMN tenant_id INTEGER" in sql
    assert "FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE" in sql
    assert "FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE SET NULL" in sql
    assert migration_mod.LEGACY_TENANT_NAME in sql
    assert "DROP TABLE" not in sql


def _seed_legacy_records_across_all_tables(engine) -> None:
    """Populates a disposable pre-SaaS database with linked legacy rows across all 19 tables."""
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO roles (id, code, name, is_active) VALUES (1, 'ADMIN', 'Admin', 1)")
        conn.exec_driver_sql("INSERT INTO ciudades (id, name, is_active) VALUES (1, 'Santa Cruz', 1)")
        conn.exec_driver_sql("INSERT INTO tallas (id, name, size_type, sort_order, is_active) VALUES (1, 'M', 'ALPHA', 30, 1)")
        conn.exec_driver_sql("INSERT INTO colores (id, name, hex_code, is_active) VALUES (1, 'Azul', '#0000FF', 1)")
        conn.exec_driver_sql(
            "INSERT INTO proveedores (id, trade_name, legal_name, tax_id, email, phone, address, is_active) "
            "VALUES (1, 'Textiles Sur', 'Textiles Sur SRL', 'NIT-100', 'sur@textiles.com', '70000100', 'Zona Ind', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO usuarios (id, role_id, first_name, last_name, email, phone, password_hash, is_active) "
            "VALUES (1, 1, 'Legacy', 'Admin', 'legacy@fashionstore.local', '70000000', 'hash', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO sucursales (id, city_id, name, address, phone, is_active) "
            "VALUES (1, 1, 'Sucursal Central', 'Av. Principal 100', '70000001', 1)"
        )
        conn.exec_driver_sql("INSERT INTO usuario_sucursales (user_id, branch_id) VALUES (1, 1)")
        conn.exec_driver_sql(
            "INSERT INTO categorias (id, name, description, is_active) VALUES (1, 'Camisas', 'Cat', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO temporadas (id, name, starts_on, ends_on, is_active) "
            "VALUES (1, 'Invierno 2026', '2026-06-01', '2026-08-31', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO colecciones (id, season_id, name, description, is_active) "
            "VALUES (1, 1, 'Lana Premium', 'Col', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO productos (id, category_id, season_id, collection_id, code, name, slug, price, is_active) "
            "VALUES (1, 1, 1, 1, 'CAM-001', 'Camisa Clasica', 'camisa-clasica', 150.00, 1)"
        )
        conn.exec_driver_sql("INSERT INTO producto_proveedores (product_id, supplier_id) VALUES (1, 1)")
        conn.exec_driver_sql(
            "INSERT INTO variantes_producto (id, product_id, size_id, color_id, sku, is_active) "
            "VALUES (1, 1, 1, 1, 'CAM-001-M-AZUL', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO ofertas_abastecimiento (id, supplier_id, product_variant_id, season_id, collection_id, status, available_quantity, is_active) "
            "VALUES (1, 1, 1, 1, 1, 'AVAILABLE', 25, 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO inventario (id, branch_id, product_variant_id, stock_quantity, reserved_quantity) "
            "VALUES (1, 1, 1, 20, 0)"
        )
        conn.exec_driver_sql(
            "INSERT INTO reservas (id, customer_id, branch_id, status) VALUES (1, 1, 1, 'PENDING')"
        )
        conn.exec_driver_sql(
            "INSERT INTO carritos (id, customer_id, status) VALUES (1, 1, 'ACTIVE')"
        )
        conn.exec_driver_sql(
            "INSERT INTO ventas (id, order_number, customer_id, branch_id, cashier_id, reservation_id, channel, subtotal, discount, total) "
            "VALUES (1, 'ORD-LEGACY-1', 1, 1, 1, 1, 'POS', 150.00, 0.00, 150.00)"
        )
        conn.exec_driver_sql(
            "INSERT INTO pagos (id, sale_id, method, provider, transaction_reference, idempotency_key, status, amount) "
            "VALUES (1, 1, 'QR', 'QR_SIMPLE', 'TX-LEG-1', 'IDEMP-LEG-1', 'PAID', 150.00)"
        )
        conn.exec_driver_sql(
            "INSERT INTO movimientos_inventario (id, inventory_id, movement_type, quantity, stock_before, stock_after, created_by) "
            "VALUES (1, 1, 'IN', 20, 0, 20, 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO promociones (id, name, discount_type, discount_value, starts_at, ends_at, is_active) "
            "VALUES (1, 'Promo Invierno', 'PERCENTAGE', 10.00, '2026-06-01 00:00:00', '2026-08-31 23:59:59', 1)"
        )
        conn.exec_driver_sql("INSERT INTO productos_promocion (promotion_id, product_id) VALUES (1, 1)")
        conn.exec_driver_sql(
            "INSERT INTO sesiones_vestidor_virtual (id, customer_id, product_id, status) VALUES (1, 1, 1, 'COMPLETED')"
        )
        conn.exec_driver_sql(
            "INSERT INTO recomendaciones_ia (id, customer_id, product_id, source) VALUES (1, 1, 1, 'trending')"
        )
        conn.exec_driver_sql(
            "INSERT INTO bitacora (id, usuario_id, accion, tipo_entidad, entidad_id) VALUES (1, 1, 'CREATE', 'Product', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO bitacora (id, usuario_id, accion, tipo_entidad, entidad_id) VALUES (2, NULL, 'SYSTEM_BOOT', 'Platform', NULL)"
        )


def test_t1_1_7_backfill_and_constraints_migration_exists_and_revises_t1_1_6():
    from pathlib import Path
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config()
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    rev = script_dir.get_revision("q8m1n4p6r8s0")
    assert rev is not None, "Expected revision q8m1n4p6r8s0 for T1.1.7 backfill and final constraints migration"
    assert rev.down_revision == "p7l0m3n5q7r9"
    assert "q8m1n4p6r8s0" in {r.revision for r in script_dir.walk_revisions()}


def test_t1_1_7_backfill_verifies_relations_and_applies_not_null_and_final_constraints(monkeypatch):
    import importlib
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import inspect, text

    m_t116 = importlib.import_module("backend.migrations.versions.p7l0m3n5q7r9_agregar_fundacion_saas_aditiva")
    m_t117 = importlib.import_module("backend.migrations.versions.q8m1n4p6r8s0_backfill_tenant_legado_y_restricciones")

    engine = create_engine("sqlite:///:memory:")
    _create_pre_t1_1_6_schema(engine)
    _seed_legacy_records_across_all_tables(engine)

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(m_t116, "op", op_proxy)
        m_t116.upgrade()
        monkeypatch.setattr(m_t117, "op", op_proxy)
        m_t117.upgrade()

    inspector = inspect(engine)
    strict_not_null_tables = {
        "sucursales",
        "categorias",
        "proveedores",
        "temporadas",
        "promociones",
        "colecciones",
        "productos",
        "variantes_producto",
        "ofertas_abastecimiento",
        "inventario",
        "reservas",
        "carritos",
        "ventas",
        "pagos",
        "movimientos_inventario",
        "sesiones_vestidor_virtual",
        "recomendaciones_ia",
    }
    for tname in strict_not_null_tables:
        cols = {c["name"]: c for c in inspector.get_columns(tname)}
        assert cols["tenant_id"]["nullable"] is False, f"{tname}.tenant_id must be NOT NULL after T1.1.7"

    # usuarios and bitacora keep nullable=True to allow platform-level identities/audit events
    assert {c["name"]: c for c in inspector.get_columns("usuarios")}["tenant_id"]["nullable"] is True
    assert {c["name"]: c for c in inspector.get_columns("bitacora")}["tenant_id"]["nullable"] is True

    with engine.begin() as conn:
        legacy_tenant_id = conn.execute(
            text("SELECT id FROM tenants WHERE name = :name"), {"name": m_t116.LEGACY_TENANT_NAME}
        ).scalar_one()

        for tname in strict_not_null_tables | {"usuarios"}:
            tid = conn.execute(text(f"SELECT tenant_id FROM {tname} WHERE id = 1")).scalar_one()
            assert tid == legacy_tenant_id, f"Row in {tname} was not backfilled to legacy tenant"

        bitacora_user_tid = conn.execute(text("SELECT tenant_id FROM bitacora WHERE id = 1")).scalar_one()
        bitacora_sys_tid = conn.execute(text("SELECT tenant_id FROM bitacora WHERE id = 2")).scalar_one()
        assert bitacora_user_tid == legacy_tenant_id
        assert bitacora_sys_tid is None

        # A second tenant can reuse the same business keys without collision
        conn.exec_driver_sql("INSERT INTO tenants (id, name, status) VALUES (2, 'Empresa Dos', 'ACTIVE')")
        conn.exec_driver_sql(
            "INSERT INTO usuarios (id, tenant_id, role_id, first_name, last_name, email, phone, password_hash, is_active) "
            "VALUES (2, 2, 1, 'Otro', 'Admin', 'legacy@fashionstore.local', '70000999', 'hash', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO sucursales (id, tenant_id, city_id, name, address, phone, is_active) "
            "VALUES (2, 2, 1, 'Sucursal Central', 'Otra Dir', '70000998', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO categorias (id, tenant_id, name, description, is_active) VALUES (2, 2, 'Camisas', 'Cat 2', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO productos (id, tenant_id, category_id, code, name, slug, price, is_active) "
            "VALUES (2, 2, 2, 'CAM-001', 'Camisa Dos', 'camisa-clasica', 180.00, 1)"
        )

    # Duplicate business key within the same legacy tenant must fail
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.exec_driver_sql(
                f"INSERT INTO categorias (tenant_id, name, is_active) VALUES ({legacy_tenant_id}, 'Camisas', 1)"
            )

    # Remove the second tenant's rows before testing downgrade back to legacy single-tenant schema
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM productos WHERE tenant_id = 2")
        conn.exec_driver_sql("DELETE FROM categorias WHERE tenant_id = 2")
        conn.exec_driver_sql("DELETE FROM sucursales WHERE tenant_id = 2")
        conn.exec_driver_sql("DELETE FROM usuarios WHERE tenant_id = 2")
        conn.exec_driver_sql("DELETE FROM tenants WHERE id = 2")

        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(m_t117, "op", op_proxy)
        m_t117.downgrade()

    inspector_after = inspect(engine)
    for tname in strict_not_null_tables:
        cols = {c["name"]: c for c in inspector_after.get_columns(tname)}
        assert cols["tenant_id"]["nullable"] is True, f"{tname}.tenant_id should be nullable again after T1.1.7 downgrade"


def test_t1_1_7_rejects_cross_tenant_relationship_mismatch_before_applying_constraints(monkeypatch):
    import importlib
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    m_t116 = importlib.import_module("backend.migrations.versions.p7l0m3n5q7r9_agregar_fundacion_saas_aditiva")
    m_t117 = importlib.import_module("backend.migrations.versions.q8m1n4p6r8s0_backfill_tenant_legado_y_restricciones")

    engine = create_engine("sqlite:///:memory:")
    _create_pre_t1_1_6_schema(engine)
    _seed_legacy_records_across_all_tables(engine)

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(m_t116, "op", op_proxy)
        m_t116.upgrade()

        # Introduce a second tenant and corrupt a relationship (product in tenant 2 pointing to category in tenant 1)
        conn.exec_driver_sql("INSERT INTO tenants (id, name, status) VALUES (99, 'Tenant Inconsistente', 'ACTIVE')")
        conn.exec_driver_sql("UPDATE productos SET tenant_id = 99 WHERE id = 1")

        monkeypatch.setattr(m_t117, "op", op_proxy)
        with pytest.raises(RuntimeError, match="inconsistencia|mismatch|relaci"):
            m_t117.upgrade()


def test_t1_1_8_seed_saas_plans_and_demo_tenants_is_idempotent_and_isolated_from_legacy_tenant():
    from app.core.models import City, Role
    from app.core.seed import (
        DEMO_TENANT_ONE_NAME,
        DEMO_TENANT_TWO_NAME,
        LEGACY_TENANT_NAME,
        seed_saas_plans_and_demo_tenants,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        legacy_tenant = Tenant(name=LEGACY_TENANT_NAME, status="ACTIVE")
        role_admin = Role(code="ADMIN", name="Administrador")
        city_sc = City(name="Santa Cruz")
        session.add_all([legacy_tenant, role_admin, city_sc])
        session.flush()

        legacy_user = User(
            tenant=legacy_tenant,
            role=role_admin,
            first_name="Admin",
            last_name="Legado",
            email="admin@fashionstore.local",
            phone="70000000",
            password_hash="hash",
        )
        legacy_branch = Branch(
            tenant=legacy_tenant,
            city=city_sc,
            name="FashionStore Centro",
            address="Av. Principal 100",
            phone="70001001",
        )
        legacy_cat = Category(tenant=legacy_tenant, name="Legado Abrigos")
        session.add_all([legacy_user, legacy_branch, legacy_cat])
        session.commit()

        # Run seed twice to verify idempotency
        seed_saas_plans_and_demo_tenants(session)
        session.commit()
        seed_saas_plans_and_demo_tenants(session)
        session.commit()

        plans = {p.code: p for p in session.query(SubscriptionPlan).all()}
        assert set(plans.keys()) == {"BASIC", "PROFESSIONAL"}
        assert plans["BASIC"].max_active_branches == 2
        assert plans["BASIC"].generative_reports_enabled is False
        assert plans["BASIC"].is_active is True
        assert plans["BASIC"].price_monthly == Decimal("199.00")
        assert plans["BASIC"].price_annual == Decimal("1990.00")
        assert plans["BASIC"].currency == "BOB"
        assert plans["PROFESSIONAL"].max_active_branches == 10
        assert plans["PROFESSIONAL"].generative_reports_enabled is True
        assert plans["PROFESSIONAL"].is_active is True
        assert plans["PROFESSIONAL"].price_monthly == Decimal("499.00")
        assert plans["PROFESSIONAL"].price_annual == Decimal("4990.00")
        assert plans["PROFESSIONAL"].currency == "BOB"

        tenants = {t.name: t for t in session.query(Tenant).all()}
        assert set(tenants.keys()) == {LEGACY_TENANT_NAME, DEMO_TENANT_ONE_NAME, DEMO_TENANT_TWO_NAME}

        t_legacy = tenants[LEGACY_TENANT_NAME]
        t_one = tenants[DEMO_TENANT_ONE_NAME]
        t_two = tenants[DEMO_TENANT_TWO_NAME]
        assert len({t_legacy.id, t_one.id, t_two.id}) == 3

        # Legacy data must remain untouched and belong strictly to Empresa Legado
        session.refresh(legacy_user)
        session.refresh(legacy_branch)
        session.refresh(legacy_cat)
        assert legacy_user.tenant_id == t_legacy.id
        assert legacy_branch.tenant_id == t_legacy.id
        assert legacy_cat.tenant_id == t_legacy.id

        # Each demo company has its own active subscription, admin(s) and branches, isolated from each other and legacy
        subs_one = [s for s in t_one.subscriptions if s.status == "ACTIVE"]
        subs_two = [s for s in t_two.subscriptions if s.status == "ACTIVE"]
        assert len(subs_one) == 1 and subs_one[0].plan.code == "BASIC"
        assert len(subs_two) == 1 and subs_two[0].plan.code == "PROFESSIONAL"

        admins_one = [u for u in t_one.users if u.role.code == "ADMIN"]
        admins_two = [u for u in t_two.users if u.role.code == "ADMIN"]
        assert len(admins_one) >= 1
        assert len(admins_two) >= 1
        assert {u.tenant_id for u in t_one.users} == {t_one.id}
        assert {u.tenant_id for u in t_two.users} == {t_two.id}
        assert {u.id for u in t_one.users}.isdisjoint({u.id for u in t_two.users})
        assert {u.id for u in t_one.users}.isdisjoint({u.id for u in t_legacy.users})

        assert len(t_one.branches) >= 1
        assert len(t_two.branches) >= 1
        assert {b.tenant_id for b in t_one.branches} == {t_one.id}
        assert {b.tenant_id for b in t_two.branches} == {t_two.id}
        assert {b.id for b in t_one.branches}.isdisjoint({b.id for b in t_two.branches})
        assert {b.id for b in t_one.branches}.isdisjoint({b.id for b in t_legacy.branches})


def test_t1_1_8_full_seed_development_data_populates_legacy_and_two_demo_tenants_idempotently(monkeypatch):
    from sqlalchemy.orm import sessionmaker
    import app.core.seed as seed_mod
    from app.core.seed import (
        DEMO_TENANT_ONE_NAME,
        DEMO_TENANT_TWO_NAME,
        LEGACY_TENANT_NAME,
        seed_development_data,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(seed_mod, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(seed_mod.settings, "app_env", "development")
    monkeypatch.setattr(seed_mod.settings, "seed_admin_password", "AdminSeed123!")

    seed_development_data()
    seed_development_data()

    with Session(engine) as session:
        tenants = {t.name: t for t in session.query(Tenant).all()}
        assert {LEGACY_TENANT_NAME, DEMO_TENANT_ONE_NAME, DEMO_TENANT_TWO_NAME}.issubset(set(tenants.keys()))

        t_legacy = tenants[LEGACY_TENANT_NAME]
        t_one = tenants[DEMO_TENANT_ONE_NAME]
        t_two = tenants[DEMO_TENANT_TWO_NAME]

        # Existing FashionStore demo branches/products belong to Empresa Legado, never to the two new test companies
        legacy_branch_names = {b.name for b in t_legacy.branches}
        assert {"FashionStore Centro", "FashionStore Norte"}.issubset(legacy_branch_names)
        assert {"FashionStore Centro", "FashionStore Norte"}.isdisjoint({b.name for b in t_one.branches})
        assert {"FashionStore Centro", "FashionStore Norte"}.isdisjoint({b.name for b in t_two.branches})


def _make_isolated_api_client():
    from fastapi.testclient import TestClient
    from sqlalchemy.pool import StaticPool
    from app.core.database import get_db
    from app.core.models import Base as AppBase
    from app.main import app

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    AppBase.metadata.create_all(engine)

    def _override_db():
        with Session(engine) as session:
            yield session

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_db
    return engine, TestClient(app), previous_override


def _restore_db_override(previous_override):
    from app.core.database import get_db
    from app.main import app

    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


def test_t1_2_1_login_and_me_include_validated_tenant_membership_and_jwt_claim():
    from app.core.models import Branch as AppBranch, City, Role, Tenant as AppTenant, User as AppUser
    from app.core.security import decode_access_token, hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            city = City(name="Santa Cruz")
            t1 = AppTenant(name="Empresa Uno", status="ACTIVE")
            t2 = AppTenant(name="Empresa Dos", status="ACTIVE")
            db.add_all([role_admin, city, t1, t2])
            db.flush()

            b1 = AppBranch(tenant=t1, city=city, name="Sucursal T1", address="Dir 1", phone="70001111")
            b2 = AppBranch(tenant=t2, city=city, name="Sucursal T2", address="Dir 2", phone="70002222")
            u1 = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Ana",
                last_name="Uno",
                email="admin@empresa.com",
                phone="70000101",
                password_hash=hash_password("SecretUno1!"),
            )
            u2 = AppUser(
                tenant=t2,
                role=role_admin,
                first_name="Beto",
                last_name="Dos",
                email="admin@empresa.com",
                phone="70000202",
                password_hash=hash_password("SecretDos2!"),
            )
            u1.branches.append(b1)
            u2.branches.append(b2)
            db.add_all([b1, b2, u1, u2])
            db.commit()
            t1_id, t2_id = t1.id, t2.id

        res1 = client.post("/api/v1/auth/login", json={"email": "admin@empresa.com", "password": "SecretUno1!"})
        assert res1.status_code == 200
        body1 = res1.json()
        assert body1["user"]["tenant_id"] == t1_id
        assert body1["user"]["tenant"] == {"id": t1_id, "name": "Empresa Uno", "status": "ACTIVE"}

        decoded1 = decode_access_token(body1["access_token"])
        assert decoded1 is not None
        assert decoded1["tenant_id"] == t1_id

        me1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body1['access_token']}"})
        assert me1.status_code == 200
        me1_body = me1.json()
        assert me1_body["tenant_id"] == t1_id
        assert me1_body["tenant"] == {"id": t1_id, "name": "Empresa Uno", "status": "ACTIVE"}
        assert [b["name"] for b in me1_body["branches"]] == ["Sucursal T1"]

        res2 = client.post("/api/v1/auth/login", json={"email": "admin@empresa.com", "password": "SecretDos2!"})
        assert res2.status_code == 200
        assert res2.json()["user"]["tenant_id"] == t2_id
    finally:
        _restore_db_override(prev)


def test_t1_2_1_auth_rejects_tampered_jwt_tenant_claim_and_spoofed_client_tenant_ids():
    from app.core.models import Role, Tenant as AppTenant, User as AppUser
    from app.core.security import create_access_token, decode_access_token, hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            t1 = AppTenant(name="Empresa Real", status="ACTIVE")
            t2 = AppTenant(name="Empresa Ajena", status="ACTIVE")
            db.add_all([role_admin, t1, t2])
            db.flush()

            u1 = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Ana",
                last_name="Real",
                email="ana@real.com",
                phone="70000101",
                password_hash=hash_password("RealPass1!"),
            )
            db.add(u1)
            db.commit()
            u1_id, t1_id, t2_id = u1.id, t1.id, t2.id

        login_res = client.post("/api/v1/auth/login", json={"email": "ana@real.com", "password": "RealPass1!"})
        assert login_res.status_code == 200
        valid_token = login_res.json()["access_token"]
        payload = decode_access_token(valid_token)
        assert payload is not None

        # Forge a token keeping the valid session jti and user sub, but claiming tenant_id = t2_id
        tampered_token = create_access_token(u1_id, "ADMIN", str(payload["jti"]), tenant_id=t2_id)
        tampered_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        assert tampered_me.status_code == 401

        # Attempt to spoof another tenant via X-Tenant-Id header or tenant_id query parameter
        spoof_header = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}", "X-Tenant-Id": str(t2_id)},
        )
        assert spoof_header.status_code == 403
        assert spoof_header.json()["detail"]["code"] == "TENANT_SCOPE_FORBIDDEN"

        spoof_query = client.get(
            f"/api/v1/auth/me?tenant_id={t2_id}",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert spoof_query.status_code == 403
        assert spoof_query.json()["detail"]["code"] == "TENANT_SCOPE_FORBIDDEN"

        # Matching tenant_id in header/query is allowed and resolves to t1_id
        matching_header = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}", "X-Tenant-Id": str(t1_id)},
        )
        assert matching_header.status_code == 200
        assert matching_header.json()["tenant_id"] == t1_id
    finally:
        _restore_db_override(prev)


def test_t1_2_1_inactive_or_suspended_tenant_blocks_login_refresh_and_session():
    from app.core.models import Role, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            t1 = AppTenant(name="Empresa Suspendible", status="ACTIVE")
            db.add_all([role_admin, t1])
            db.flush()

            u1 = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Carlos",
                last_name="Tenant",
                email="carlos@suspendible.com",
                phone="70000303",
                password_hash=hash_password("CarlosPass1!"),
            )
            db.add(u1)
            db.commit()
            t1_id = t1.id

        login_ok = client.post("/api/v1/auth/login", json={"email": "carlos@suspendible.com", "password": "CarlosPass1!"})
        assert login_ok.status_code == 200
        access_token = login_ok.json()["access_token"]
        refresh_token = login_ok.json()["refresh_token"]

        # Suspend the tenant in DB
        with Session(engine) as db:
            tenant = db.get(AppTenant, t1_id)
            assert tenant is not None
            tenant.status = "SUSPENDED"
            db.commit()

        # Existing session, refresh, and new login must all be rejected when tenant is not ACTIVE
        me_suspended = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_suspended.status_code == 403
        assert me_suspended.json()["detail"]["code"] == "TENANT_INACTIVE"

        refresh_suspended = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_suspended.status_code == 403
        assert refresh_suspended.json()["detail"]["code"] == "TENANT_INACTIVE"

        login_suspended = client.post("/api/v1/auth/login", json={"email": "carlos@suspendible.com", "password": "CarlosPass1!"})
        assert login_suspended.status_code == 403
        assert login_suspended.json()["detail"]["code"] == "TENANT_INACTIVE"
    finally:
        _restore_db_override(prev)


def test_t1_2_2_platform_admin_role_and_permissions_are_strictly_separated_from_tenant_admin():
    from app.modules.auth.dependencies import (
        PLATFORM_ADMIN_ROLE,
        PLATFORM_PERMISSIONS as DEP_PLATFORM_PERMISSIONS,
        TENANT_ADMIN_ROLE,
    )
    from app.core.seed import (
        PERMISSIONS,
        PLATFORM_PERMISSIONS,
        ROLE_PERMISSIONS,
        ROLES,
        TENANT_PERMISSIONS,
    )

    assert PLATFORM_ADMIN_ROLE == "PLATFORM_ADMIN"
    assert TENANT_ADMIN_ROLE == "ADMIN"
    assert "PLATFORM_ADMIN" in ROLES
    assert "ADMIN" in ROLES
    assert ROLES["PLATFORM_ADMIN"] != ROLES["ADMIN"]

    expected_platform_perms = {"saas.tenants.manage", "saas.plans.manage", "saas.subscriptions.manage"}
    assert expected_platform_perms.issubset(set(PLATFORM_PERMISSIONS.keys()))
    assert set(DEP_PLATFORM_PERMISSIONS) == set(PLATFORM_PERMISSIONS.keys())
    assert set(PLATFORM_PERMISSIONS.keys()).isdisjoint(set(TENANT_PERMISSIONS.keys()))
    assert set(PERMISSIONS.keys()) == set(TENANT_PERMISSIONS.keys()) | set(PLATFORM_PERMISSIONS.keys())

    assert ROLE_PERMISSIONS["ADMIN"] == set(TENANT_PERMISSIONS.keys())
    assert ROLE_PERMISSIONS["ADMIN"].isdisjoint(set(PLATFORM_PERMISSIONS.keys()))
    assert ROLE_PERMISSIONS["PLATFORM_ADMIN"] == set(PLATFORM_PERMISSIONS.keys())
    assert ROLE_PERMISSIONS["PLATFORM_ADMIN"].isdisjoint(set(TENANT_PERMISSIONS.keys()))


def test_t1_2_2_company_admin_is_rejected_on_platform_routes_and_cannot_escalate_to_platform_admin():
    from typing import Annotated
    from fastapi import APIRouter, Depends
    from app.core.models import Permission, Role, RolePermission, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password
    from app.main import app
    from app.modules.auth.dependencies import require_platform_admin, require_platform_permission

    engine, client, prev = _make_isolated_api_client()
    temp_router = APIRouter(prefix="/api/v1/platform/_test_t122_guard")

    @temp_router.get("/admin-only")
    def _platform_admin_only(actor: Annotated[AppUser, Depends(require_platform_admin)]):
        return {"actor_id": actor.id, "role": actor.role.code}

    @temp_router.get("/tenants-manage")
    def _platform_tenants_manage(actor: Annotated[AppUser, Depends(require_platform_permission("saas.tenants.manage"))]):
        return {"actor_id": actor.id}

    app.include_router(temp_router)
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_client = Role(code="CLIENT", name="Cliente")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador de Plataforma SaaS")
            perm_tenants = Permission(code="saas.tenants.manage", name="Gestionar empresas SaaS")
            db.add_all([role_admin, role_client, role_platform, perm_tenants])
            db.flush()
            db.add(RolePermission(role_id=role_platform.id, permission_id=perm_tenants.id))

            t1 = AppTenant(name="Empresa Uno", status="ACTIVE")
            db.add(t1)
            db.flush()

            company_admin = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Admin",
                last_name="Empresa",
                email="admin@empresauno.com",
                phone="70001001",
                password_hash=hash_password("EmpresaAdmin1!"),
            )
            regular_user = AppUser(
                tenant=t1,
                role=role_client,
                first_name="Cliente",
                last_name="Empresa",
                email="cliente@empresauno.com",
                phone="70001002",
                password_hash=hash_password("ClientePass1!"),
            )
            platform_admin = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Root",
                last_name="SaaS",
                email="root@saas.platform",
                phone="70009999",
                password_hash=hash_password("PlatformRoot1!"),
            )
            db.add_all([company_admin, regular_user, platform_admin])
            db.commit()
            regular_user_id, platform_admin_id = regular_user.id, platform_admin.id

        admin_login = client.post("/api/v1/auth/login", json={"email": "admin@empresauno.com", "password": "EmpresaAdmin1!"})
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Company ADMIN cannot access platform-only routes
        res_guard1 = client.get("/api/v1/platform/_test_t122_guard/admin-only", headers=admin_headers)
        assert res_guard1.status_code == 403
        assert res_guard1.json()["detail"]["code"] == "PLATFORM_ADMIN_REQUIRED"

        res_guard2 = client.get("/api/v1/platform/_test_t122_guard/tenants-manage", headers=admin_headers)
        assert res_guard2.status_code == 403
        assert res_guard2.json()["detail"]["code"] == "PLATFORM_ADMIN_REQUIRED"

        # Company ADMIN cannot create or update a user with PLATFORM_ADMIN role
        create_escalation = client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "first_name": "Intruso",
                "last_name": "SaaS",
                "email": "intruso@empresauno.com",
                "phone": "70001099",
                "password": "IntrusoPass1!",
                "role": "PLATFORM_ADMIN",
            },
        )
        assert create_escalation.status_code == 403
        assert create_escalation.json()["detail"]["code"] == "PLATFORM_ROLE_ASSIGNMENT_FORBIDDEN"

        update_escalation = client.patch(
            f"/api/v1/users/{regular_user_id}",
            headers=admin_headers,
            json={"role": "PLATFORM_ADMIN"},
        )
        assert update_escalation.status_code == 403
        assert update_escalation.json()["detail"]["code"] == "PLATFORM_ROLE_ASSIGNMENT_FORBIDDEN"

        # Platform admin accounts are invisible and unreachable from tenant user management
        users_list = client.get("/api/v1/users", headers=admin_headers)
        assert users_list.status_code == 200
        listed_emails = {u["email"] for u in users_list.json()["items"]}
        assert "root@saas.platform" not in listed_emails
        assert client.get(f"/api/v1/users/{platform_admin_id}", headers=admin_headers).status_code == 404
        assert client.patch(f"/api/v1/users/{platform_admin_id}/deactivate", headers=admin_headers).status_code == 404
    finally:
        app.router.routes[:] = [r for r in app.router.routes if not getattr(r, "path", "").startswith("/api/v1/platform/_test_t122_guard")]
        _restore_db_override(prev)


def test_t1_2_2_platform_admin_cannot_access_tenant_operational_routes_and_cross_tenant_is_reserved_for_explicit_platform_routes():
    from typing import Annotated
    from fastapi import APIRouter, Depends
    from sqlalchemy import select
    from app.core.models import (
        Bitacora,
        Branch as AppBranch,
        City,
        Permission,
        Role,
        RolePermission,
        Tenant as AppTenant,
        User as AppUser,
    )
    from app.core.security import hash_password
    from app.main import app
    from app.modules.auth.dependencies import require_branch_access, resolve_platform_target_tenant

    engine, client, prev = _make_isolated_api_client()
    temp_router = APIRouter()

    @temp_router.get("/api/v1/platform/_test_t122_ops/tenants/{target_tenant_id}/inspect")
    def _platform_inspect_tenant(
        target_tenant: Annotated[AppTenant, Depends(resolve_platform_target_tenant("saas.tenants.manage"))],
    ):
        return {"target_tenant_id": target_tenant.id, "target_tenant_name": target_tenant.name}

    @temp_router.get("/api/v1/platform/_test_t122_ops/inspect-by-header")
    def _platform_inspect_by_header(
        target_tenant: Annotated[AppTenant, Depends(resolve_platform_target_tenant("saas.subscriptions.manage"))],
    ):
        return {"target_tenant_id": target_tenant.id, "target_tenant_name": target_tenant.name}

    @temp_router.get("/api/v1/_test_t122_non_platform_cross_tenant")
    def _misconfigured_non_platform_route(
        target_tenant: Annotated[AppTenant, Depends(resolve_platform_target_tenant("saas.tenants.manage"))],
    ):
        return {"target_tenant_id": target_tenant.id}

    @temp_router.get("/api/v1/_test_t122_branch_check/{branch_id}")
    def _tenant_branch_route(
        branch_id: int,
        user: Annotated[AppUser, Depends(require_branch_access)],
    ):
        return {"user_id": user.id, "branch_id": branch_id}

    app.include_router(temp_router)
    try:
        with Session(engine) as db:
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador de Plataforma SaaS")
            perm_tenants = Permission(code="saas.tenants.manage", name="Gestionar empresas SaaS")
            perm_subs = Permission(code="saas.subscriptions.manage", name="Gestionar suscripciones SaaS", is_active=False)
            city = City(name="Santa Cruz")
            t1 = AppTenant(name="Boutique Uno", status="ACTIVE")
            t2 = AppTenant(name="Boutique Dos", status="ACTIVE")
            db.add_all([role_platform, perm_tenants, perm_subs, city, t1, t2])
            db.flush()
            db.add_all([
                RolePermission(role_id=role_platform.id, permission_id=perm_tenants.id),
                RolePermission(role_id=role_platform.id, permission_id=perm_subs.id),
            ])
            b1 = AppBranch(tenant=t1, city=city, name="Sucursal Uno", address="Dir 1", phone="70001111")
            platform_user = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Saas",
                last_name="Operator",
                email="operator@saas.platform",
                phone="70008888",
                password_hash=hash_password("SaasOperator1!"),
            )
            db.add_all([b1, platform_user])
            db.commit()
            t1_id, t2_id, b1_id, platform_user_id = t1.id, t2.id, b1.id, platform_user.id

        login_res = client.post("/api/v1/auth/login", json={"email": "operator@saas.platform", "password": "SaasOperator1!"})
        assert login_res.status_code == 200
        login_body = login_res.json()
        assert login_body["user"]["role"] == "PLATFORM_ADMIN"
        assert login_body["user"]["tenant_id"] is None
        assert login_body["user"]["tenant"] is None
        platform_headers = {"Authorization": f"Bearer {login_body['access_token']}"}

        # 1. PLATFORM_ADMIN is rejected on tenant operational routes (require_permission, require_admin, require_branch_access)
        assert client.get("/api/v1/users", headers=platform_headers).status_code == 403
        assert client.post("/api/v1/categories", headers=platform_headers, json={"name": "Cat SaaS"}).status_code == 403
        assert client.get(f"/api/v1/_test_t122_branch_check/{b1_id}", headers=platform_headers).status_code == 403

        # 2. PLATFORM_ADMIN cannot pass X-Tenant-Id or ?tenant_id= on non-platform routes
        spoof_non_platform = client.get(
            "/api/v1/auth/me",
            headers={**platform_headers, "X-Tenant-Id": str(t1_id)},
        )
        assert spoof_non_platform.status_code == 403
        assert spoof_non_platform.json()["detail"]["code"] in {"CROSS_TENANT_PLATFORM_ROUTE_REQUIRED", "TENANT_SCOPE_FORBIDDEN"}

        # 3. Cross-tenant resolver on a non-platform path is rejected even for PLATFORM_ADMIN
        non_platform_cross = client.get(
            f"/api/v1/_test_t122_non_platform_cross_tenant?target_tenant_id={t1_id}",
            headers=platform_headers,
        )
        assert non_platform_cross.status_code == 403
        assert non_platform_cross.json()["detail"]["code"] == "CROSS_TENANT_PLATFORM_ROUTE_REQUIRED"

        # 4. On explicit platform route, missing target tenant is rejected with 400 TARGET_TENANT_REQUIRED,
        # and inactive/missing platform permission is rejected with 403 PLATFORM_PERMISSION_REQUIRED
        missing_perm = client.get(
            f"/api/v1/platform/_test_t122_ops/inspect-by-header?target_tenant_id={t1_id}",
            headers=platform_headers,
        )
        assert missing_perm.status_code == 403
        assert missing_perm.json()["detail"]["code"] == "PLATFORM_PERMISSION_REQUIRED"

        # Activate saas.subscriptions.manage to test missing target tenant vs explicit target tenant
        with Session(engine) as db:
            perm = db.scalar(select(Permission).where(Permission.code == "saas.subscriptions.manage"))
            assert perm is not None
            perm.is_active = True
            db.commit()

        missing_target = client.get("/api/v1/platform/_test_t122_ops/inspect-by-header", headers=platform_headers)
        assert missing_target.status_code == 400
        assert missing_target.json()["detail"]["code"] == "TARGET_TENANT_REQUIRED"

        # 5. Authorized explicit platform route resolves target tenant and records audit event in Bitacora
        ok_t1 = client.get(f"/api/v1/platform/_test_t122_ops/tenants/{t1_id}/inspect", headers=platform_headers)
        assert ok_t1.status_code == 200
        assert ok_t1.json() == {"target_tenant_id": t1_id, "target_tenant_name": "Boutique Uno"}

        ok_t2 = client.get(
            "/api/v1/platform/_test_t122_ops/inspect-by-header",
            headers={**platform_headers, "X-Target-Tenant-Id": str(t2_id)},
        )
        assert ok_t2.status_code == 200
        assert ok_t2.json() == {"target_tenant_id": t2_id, "target_tenant_name": "Boutique Dos"}

        with Session(engine) as db:
            audits = db.scalars(
                select(Bitacora)
                .where(Bitacora.user_id == platform_user_id, Bitacora.action == "PLATFORM_TARGET_ACCESS")
                .order_by(Bitacora.id.asc())
            ).all()
            assert len(audits) == 2
            assert audits[0].tenant_id == t1_id
            assert audits[0].entity_type == "tenant"
            assert audits[0].entity_id == t1_id
            assert audits[0].new_values["permission"] == "saas.tenants.manage"
            assert audits[1].tenant_id == t2_id
            assert audits[1].new_values["permission"] == "saas.subscriptions.manage"
    finally:
        app.router.routes[:] = [
            r
            for r in app.router.routes
            if not getattr(r, "path", "").startswith("/api/v1/platform/_test_t122_ops")
            and not getattr(r, "path", "").startswith("/api/v1/_test_t122_")
        ]
        _restore_db_override(prev)


def _seed_two_tenants_with_full_operational_data(db: Session):
    from datetime import UTC, date, datetime, timedelta
    from decimal import Decimal
    from app.core.models import (
        Bitacora,
        Branch as AppBranch,
        Category as AppCategory,
        City,
        Collection as AppCollection,
        Color,
        Inventory as AppInventory,
        Permission,
        Product as AppProduct,
        ProductImage,
        ProductVariant as AppProductVariant,
        Promotion as AppPromotion,
        Reservation as AppReservation,
        Role,
        RolePermission,
        Sale as AppSale,
        Season as AppSeason,
        Size,
        Supplier as AppSupplier,
        Tenant as AppTenant,
        User as AppUser,
    )
    from app.core.security import hash_password

    role_admin = Role(code="ADMIN", name="Administrador")
    role_client = Role(code="CLIENT", name="Cliente")
    role_manager = Role(code="BRANCH_MANAGER", name="Encargado")
    perms = [
        Permission(code="cart.manage", name="Carrito"),
        Permission(code="reservations.read", name="Reservas leer"),
        Permission(code="reservations.create", name="Reservas crear"),
        Permission(code="sales.read", name="Ventas leer"),
        Permission(code="payments.electronic", name="Pagos electronicos"),
    ]
    city = City(name="Santa Cruz")
    size_m = Size(name="M", size_type="ALPHA", sort_order=30)
    color_negro = Color(name="Negro", hex_code="#000000")
    t_a = AppTenant(name="Tenant Alpha", status="ACTIVE")
    t_b = AppTenant(name="Tenant Beta", status="ACTIVE")
    db.add_all([role_admin, role_client, role_manager, *perms, city, size_m, color_negro, t_a, t_b])
    db.flush()
    for p in perms:
        db.add(RolePermission(role_id=role_client.id, permission_id=p.id))

    data: dict[str, dict[str, int]] = {"A": {}, "B": {}}
    for label, tenant, suffix in (("A", t_a, "alpha"), ("B", t_b, "beta")):
        admin = AppUser(
            tenant=tenant,
            role=role_admin,
            first_name=f"Admin{label}",
            last_name="Owner",
            email=f"admin@{suffix}.com",
            phone=f"7100000{1 if label == 'A' else 2}",
            password_hash=hash_password("TenantAdmin1!"),
        )
        client_user = AppUser(
            tenant=tenant,
            role=role_client,
            first_name=f"Client{label}",
            last_name="Buyer",
            email=f"client@{suffix}.com",
            phone=f"7200000{1 if label == 'A' else 2}",
            password_hash=hash_password("TenantClient1!"),
        )
        branch = AppBranch(tenant=tenant, city=city, name=f"Sucursal {label}", address=f"Av. {label}", phone="73000001")
        category = AppCategory(tenant=tenant, name=f"Categoria {label}", description=f"Desc {label}")
        supplier = AppSupplier(tenant=tenant, trade_name=f"Proveedor {label}", tax_id=f"NIT-{label}-001")
        season = AppSeason(tenant=tenant, name=f"Temporada {label}", starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31))
        db.add_all([admin, client_user, branch, category, supplier, season])
        db.flush()

        collection = AppCollection(tenant=tenant, season_id=season.id, name=f"Coleccion {label}")
        product = AppProduct(
            tenant=tenant,
            category_id=category.id,
            season_id=season.id,
            code=f"PRD-{label}-01",
            name=f"Prenda {label}",
            slug=f"prenda-{suffix}",
            price=Decimal("150.00"),
        )
        db.add_all([collection, product])
        db.flush()

        image = ProductImage(product_id=product.id, image_url=f"https://example.com/{suffix}.jpg", is_primary=True, sort_order=0)
        variant = AppProductVariant(
            tenant=tenant,
            product_id=product.id,
            size_id=size_m.id,
            color_id=color_negro.id,
            sku=f"SKU-{label}-M-BLK",
        )
        promo = AppPromotion(
            tenant=tenant,
            name=f"Promo {label}",
            discount_type="PERCENT",
            discount_value=Decimal("10.00"),
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=5),
        )
        db.add_all([image, variant, promo])
        db.flush()

        inventory = AppInventory(tenant=tenant, branch_id=branch.id, product_variant_id=variant.id, stock_quantity=15)
        reservation = AppReservation(
            tenant=tenant,
            customer_id=client_user.id,
            branch_id=branch.id,
            status="PENDING",
            expires_at=datetime.now(UTC) + timedelta(hours=4),
        )
        sale = AppSale(
            tenant=tenant,
            order_number=f"ORD-{label}-001",
            customer_id=client_user.id,
            branch_id=branch.id,
            channel="PHYSICAL",
            status="CONFIRMED",
            subtotal=Decimal("150.00"),
            discount=Decimal("0.00"),
            total=Decimal("150.00"),
        )
        audit = Bitacora(
            tenant=tenant,
            user_id=admin.id,
            action="CREATE",
            entity_type="product",
            entity_id=product.id,
            description=f"Evento de {label}",
        )
        db.add_all([inventory, reservation, sale, audit])
        db.flush()

        data[label] = {
            "tenant_id": tenant.id,
            "admin_id": admin.id,
            "client_id": client_user.id,
            "branch_id": branch.id,
            "category_id": category.id,
            "supplier_id": supplier.id,
            "season_id": season.id,
            "collection_id": collection.id,
            "product_id": product.id,
            "image_id": image.id,
            "variant_id": variant.id,
            "promo_id": promo.id,
            "inventory_id": inventory.id,
            "reservation_id": reservation.id,
            "sale_id": sale.id,
            "city_id": city.id,
            "size_id": size_m.id,
            "color_id": color_negro.id,
        }

    db.commit()
    return data


def test_t1_2_3_tenant_isolation_blocks_cross_tenant_reads_lists_and_enumeration_across_modules():
    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            seeded = _seed_two_tenants_with_full_operational_data(db)

        a = seeded["A"]
        b = seeded["B"]

        login_a = client.post("/api/v1/auth/login", json={"email": "admin@alpha.com", "password": "TenantAdmin1!"})
        assert login_a.status_code == 200
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        # 1. Listing endpoints only return Tenant A resources, never Tenant B resources
        users_a = client.get("/api/v1/users", headers=headers_a).json()
        assert {item["id"] for item in users_a["items"]} == {a["admin_id"], a["client_id"]}

        branches_a = client.get("/api/v1/branches", headers=headers_a).json()
        assert [item["id"] for item in branches_a["items"]] == [a["branch_id"]]

        categories_a = client.get("/api/v1/categories", headers=headers_a).json()
        assert [item["id"] for item in categories_a["items"]] == [a["category_id"]]

        suppliers_a = client.get("/api/v1/suppliers", headers=headers_a).json()
        assert [item["id"] for item in suppliers_a["items"]] == [a["supplier_id"]]

        seasons_a = client.get("/api/v1/seasons", headers=headers_a).json()
        assert [item["id"] for item in seasons_a["items"]] == [a["season_id"]]

        collections_a = client.get("/api/v1/collections", headers=headers_a).json()
        assert [item["id"] for item in collections_a["items"]] == [a["collection_id"]]

        products_a = client.get("/api/v1/products", headers=headers_a).json()
        assert [item["id"] for item in products_a["items"]] == [a["product_id"]]

        promos_a = client.get("/api/v1/promotions", headers=headers_a).json()
        assert [item["id"] for item in promos_a["items"]] == [a["promo_id"]]

        inv_a = client.get("/api/v1/inventory", headers=headers_a).json()
        assert [item["id"] for item in inv_a["items"]] == [a["inventory_id"]]

        dashboard_a = client.get("/api/v1/reports/dashboard", headers=headers_a).json()
        assert dashboard_a["revenue"]["sales_count"] == 1
        assert [row["branch_id"] for row in dashboard_a["sales_by_branch"]] == [a["branch_id"]]

        audit_a = client.get("/api/v1/audit", headers=headers_a).json()
        assert audit_a["total"] == 1
        assert audit_a["items"][0]["entity_id"] == a["product_id"]

        catalog_a = client.get("/api/v1/catalog", headers=headers_a).json()
        assert [item["id"] for item in catalog_a["items"]] == [a["product_id"]]

        # 2. Direct GET by Tenant B IDs returns 404 Not Found (non-enumerable, indistinguishable from missing ID)
        for endpoint in (
            f"/api/v1/users/{b['client_id']}",
            f"/api/v1/branches/{b['branch_id']}",
            f"/api/v1/categories/{b['category_id']}",
            f"/api/v1/suppliers/{b['supplier_id']}",
            f"/api/v1/seasons/{b['season_id']}",
            f"/api/v1/collections/{b['collection_id']}",
            f"/api/v1/products/{b['product_id']}",
            f"/api/v1/promotions/{b['promo_id']}",
            f"/api/v1/inventory/{b['inventory_id']}",
            f"/api/v1/reservations/{b['reservation_id']}",
            f"/api/v1/sales/{b['sale_id']}",
            f"/api/v1/catalog/{b['product_id']}",
        ):
            res = client.get(endpoint, headers=headers_a)
            assert res.status_code == 404, f"Expected 404 for cross-tenant GET {endpoint}, got {res.status_code}: {res.text}"

        # 3. Tenant B logged in immediately after Tenant A sees only Tenant B resources and gets 404 on Tenant A IDs
        login_b = client.post("/api/v1/auth/login", json={"email": "admin@beta.com", "password": "TenantAdmin1!"})
        assert login_b.status_code == 200
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
        assert {item["id"] for item in client.get("/api/v1/users", headers=headers_b).json()["items"]} == {b["admin_id"], b["client_id"]}
        assert [item["id"] for item in client.get("/api/v1/products", headers=headers_b).json()["items"]] == [b["product_id"]]
        assert [item["id"] for item in client.get("/api/v1/catalog", headers=headers_b).json()["items"]] == [b["product_id"]]
        assert client.get(f"/api/v1/products/{a['product_id']}", headers=headers_b).status_code == 404
    finally:
        _restore_db_override(prev)


def test_t1_2_3_tenant_isolation_blocks_cross_tenant_mutations_deletions_and_foreign_relationships():
    from app.core.models import Category as AppCategory, Product as AppProduct

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            seeded = _seed_two_tenants_with_full_operational_data(db)

        a = seeded["A"]
        b = seeded["B"]

        login_admin_a = client.post("/api/v1/auth/login", json={"email": "admin@alpha.com", "password": "TenantAdmin1!"})
        headers_admin_a = {"Authorization": f"Bearer {login_admin_a.json()['access_token']}"}

        login_client_a = client.post("/api/v1/auth/login", json={"email": "client@alpha.com", "password": "TenantClient1!"})
        headers_client_a = {"Authorization": f"Bearer {login_client_a.json()['access_token']}"}

        # 1. Cross-tenant mutations/deactivations/deletions on Tenant B resources are rejected with 404
        assert client.patch(f"/api/v1/users/{b['client_id']}", headers=headers_admin_a, json={"first_name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/users/{b['client_id']}/deactivate", headers=headers_admin_a).status_code == 404
        assert client.patch(f"/api/v1/branches/{b['branch_id']}", headers=headers_admin_a, json={"name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/categories/{b['category_id']}", headers=headers_admin_a, json={"name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/suppliers/{b['supplier_id']}", headers=headers_admin_a, json={"trade_name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/seasons/{b['season_id']}", headers=headers_admin_a, json={"name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/collections/{b['collection_id']}", headers=headers_admin_a, json={"name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/products/{b['product_id']}", headers=headers_admin_a, json={"name": "Hack"}).status_code == 404
        assert client.delete(f"/api/v1/products/{b['product_id']}/images/{b['image_id']}", headers=headers_admin_a).status_code == 404
        assert client.patch(f"/api/v1/promotions/{b['promo_id']}", headers=headers_admin_a, json={"name": "Hack"}).status_code == 404
        assert client.patch(f"/api/v1/inventory/{b['inventory_id']}", headers=headers_admin_a, json={"stock_quantity": 0}).status_code == 404
        assert client.patch(f"/api/v1/reservations/{b['reservation_id']}/cancel", headers=headers_admin_a).status_code == 404

        # 2. Cross-tenant foreign key/relationship references in create/update payloads are rejected
        assert client.post(
            "/api/v1/products",
            headers=headers_admin_a,
            json={
                "category_id": b["category_id"],
                "code": "CROSS-CAT",
                "name": "Cross Cat",
                "slug": "cross-cat",
                "price": "100.00",
            },
        ).status_code == 400

        assert client.post(
            "/api/v1/products",
            headers=headers_admin_a,
            json={
                "category_id": a["category_id"],
                "season_id": b["season_id"],
                "code": "CROSS-SEA",
                "name": "Cross Sea",
                "slug": "cross-sea",
                "price": "100.00",
            },
        ).status_code == 400

        assert client.post(
            "/api/v1/products",
            headers=headers_admin_a,
            json={
                "category_id": a["category_id"],
                "supplier_ids": [b["supplier_id"]],
                "code": "CROSS-SUP",
                "name": "Cross Sup",
                "slug": "cross-sup",
                "price": "100.00",
            },
        ).status_code == 400

        assert client.post(
            f"/api/v1/promotions/{a['promo_id']}/products",
            headers=headers_admin_a,
            json={"product_ids": [b["product_id"]]},
        ).status_code == 404

        assert client.post(
            "/api/v1/users",
            headers=headers_admin_a,
            json={
                "first_name": "Cajero",
                "last_name": "Cross",
                "email": "cajero.cross@alpha.com",
                "phone": "71009911",
                "password": "CajeroCross1!",
                "role": "CASHIER",
                "branch_ids": [b["branch_id"]],
            },
        ).status_code == 400

        assert client.post(
            "/api/v1/cart/items",
            headers=headers_client_a,
            json={"product_variant_id": b["variant_id"], "quantity": 1},
        ).status_code == 400

        assert client.post(
            "/api/v1/reservations",
            headers=headers_client_a,
            json={"branch_id": a["branch_id"], "items": [{"product_variant_id": b["variant_id"], "quantity": 1}]},
        ).status_code == 400

        # 3. Newly created entities in Tenant A automatically receive tenant_id = a["tenant_id"]
        # and can reuse business keys that exist in Tenant B without conflict
        new_cat = client.post(
            "/api/v1/categories",
            headers=headers_admin_a,
            json={"name": "Categoria B", "description": "Mismo nombre que en Tenant B"},
        )
        assert new_cat.status_code == 201
        new_cat_id = new_cat.json()["id"]

        new_prod = client.post(
            "/api/v1/products",
            headers=headers_admin_a,
            json={
                "category_id": new_cat_id,
                "code": "PRD-B-01",
                "name": "Prenda B en Alpha",
                "slug": "prenda-beta",
                "price": "190.00",
                "variants": [{"size_id": a["size_id"], "color_id": a["color_id"], "sku": "SKU-B-M-BLK"}],
            },
        )
        assert new_prod.status_code == 201
        new_prod_id = new_prod.json()["id"]

        with Session(engine) as db:
            saved_cat = db.get(AppCategory, new_cat_id)
            saved_prod = db.get(AppProduct, new_prod_id)
            b_prod = db.get(AppProduct, b["product_id"])
            assert saved_cat is not None and saved_cat.tenant_id == a["tenant_id"]
            assert saved_prod is not None and saved_prod.tenant_id == a["tenant_id"]
            assert b_prod is not None and b_prod.name == "Prenda B"
    finally:
        _restore_db_override(prev)


def test_t1_2_4_joint_tenant_and_branch_validation_blocks_cross_tenant_branch_id_operations_with_non_enumerable_responses():
    from sqlalchemy import select
    from app.core.models import Branch as AppBranch, City, Inventory as AppInventory, Permission, Role, RolePermission, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            seeded = _seed_two_tenants_with_full_operational_data(db)

            # Add cashier role with necessary permissions to Tenant A
            role_cashier = db.scalar(select(Role).where(Role.code == "CASHIER"))
            if role_cashier is None:
                role_cashier = Role(code="CASHIER", name="Cajero")
                db.add(role_cashier)
                db.flush()

            cashier_perms = [
                Permission(code="sales.create", name="Crear ventas"),
                Permission(code="reservations.manage", name="Gestionar reservas"),
                Permission(code="reservations.fulfill", name="Entregar reservas"),
            ]
            for p in cashier_perms:
                if not db.scalar(select(Permission).where(Permission.code == p.code)):
                    db.add(p)
            db.flush()
            for p in cashier_perms:
                perm_obj = db.scalar(select(Permission).where(Permission.code == p.code))
                if not db.scalar(select(RolePermission).where(RolePermission.role_id == role_cashier.id, RolePermission.permission_id == perm_obj.id)):
                    db.add(RolePermission(role_id=role_cashier.id, permission_id=perm_obj.id))

            t_a = db.get(AppTenant, seeded["A"]["tenant_id"])
            city = db.get(City, seeded["A"]["city_id"])
            branch_a1 = db.get(AppBranch, seeded["A"]["branch_id"])

            # Create a second branch in Tenant A
            branch_a2 = AppBranch(tenant=t_a, city=city, name="Sucursal A2 Oeste", address="Av. A2", phone="73000002")
            db.add(branch_a2)
            db.flush()

            # Cashier A assigned ONLY to branch_a1
            cashier_a = AppUser(
                tenant=t_a,
                role=role_cashier,
                first_name="Cajero",
                last_name="Alpha",
                email="cajero@alpha.com",
                phone="72000010",
                password_hash=hash_password("CashierAlpha1!"),
            )
            cashier_a.branches.append(branch_a1)
            db.add(cashier_a)
            db.commit()

            branch_a2_id = branch_a2.id
            cashier_a_id = cashier_a.id

        a = seeded["A"]
        b = seeded["B"]

        # Logins
        login_admin_a = client.post("/api/v1/auth/login", json={"email": "admin@alpha.com", "password": "TenantAdmin1!"})
        assert login_admin_a.status_code == 200
        headers_admin_a = {"Authorization": f"Bearer {login_admin_a.json()['access_token']}"}

        login_cashier_a = client.post("/api/v1/auth/login", json={"email": "cajero@alpha.com", "password": "CashierAlpha1!"})
        assert login_cashier_a.status_code == 200
        headers_cashier_a = {"Authorization": f"Bearer {login_cashier_a.json()['access_token']}"}

        login_client_a = client.post("/api/v1/auth/login", json={"email": "client@alpha.com", "password": "TenantClient1!"})
        assert login_client_a.status_code == 200
        headers_client_a = {"Authorization": f"Bearer {login_client_a.json()['access_token']}"}

        # 1. INVENTORY operations with cross-tenant branch_id return 404 (non-enumerable BRANCH_NOT_FOUND)
        res_inv_list = client.get(f"/api/v1/inventory?branch_id={b['branch_id']}", headers=headers_admin_a)
        assert res_inv_list.status_code == 404, f"Expected 404, got {res_inv_list.status_code}: {res_inv_list.text}"
        assert res_inv_list.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        res_inv_create = client.post(
            "/api/v1/inventory",
            headers=headers_admin_a,
            json={"branch_id": b["branch_id"], "product_variant_id": a["variant_id"], "stock_quantity": 10},
        )
        assert res_inv_create.status_code == 404
        assert res_inv_create.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # 2. RESERVATIONS operations with cross-tenant branch_id return 404/400 without leaking Tenant B data
        res_res_admin = client.get(f"/api/v1/reservations/branch?branch_id={b['branch_id']}", headers=headers_admin_a)
        assert res_res_admin.status_code == 404
        assert res_res_admin.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        res_res_cashier = client.get(f"/api/v1/reservations/branch?branch_id={b['branch_id']}", headers=headers_cashier_a)
        assert res_res_cashier.status_code == 404, "Must not leak 403 on another tenant's branch"
        assert res_res_cashier.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        res_res_create = client.post(
            "/api/v1/reservations",
            headers=headers_client_a,
            json={"branch_id": b["branch_id"], "items": [{"product_variant_id": a["variant_id"], "quantity": 1}]},
        )
        assert res_res_create.status_code == 400
        assert res_res_create.json()["detail"]["code"] == "BRANCH_NOT_FOUND_OR_INACTIVE"

        # 3. COMMERCE operations with cross-tenant branch_id return 404/400
        res_sale_phys = client.post(
            "/api/v1/sales/physical",
            headers=headers_cashier_a,
            json={"branch_id": b["branch_id"], "items": [{"product_variant_id": a["variant_id"], "quantity": 1}]},
        )
        assert res_sale_phys.status_code == 404
        assert res_sale_phys.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # Put an item into client A's cart first
        add_cart = client.post(
            "/api/v1/cart/items",
            headers=headers_client_a,
            json={"product_variant_id": a["variant_id"], "quantity": 1},
        )
        assert add_cart.status_code == 200

        res_purchase_dig = client.post(
            "/api/v1/purchases/digital",
            headers=headers_client_a,
            json={"branch_id": b["branch_id"]},
        )
        assert res_purchase_dig.status_code == 400
        assert res_purchase_dig.json()["detail"]["code"] == "BRANCH_NOT_FOUND_OR_INACTIVE"

        # 4. REPORTS operations with cross-tenant branch_id return 404 Not Found
        for report_route in (
            f"/api/v1/reports/dashboard?branch_id={b['branch_id']}",
            f"/api/v1/reports/sales-by-branch?branch_id={b['branch_id']}",
            f"/api/v1/reports/top-products?branch_id={b['branch_id']}",
            f"/api/v1/reports/low-stock?branch_id={b['branch_id']}",
            f"/api/v1/reports/reservations-summary?branch_id={b['branch_id']}",
            f"/api/v1/reports/sales-by-channel?branch_id={b['branch_id']}",
            f"/api/v1/reports/revenue-summary?branch_id={b['branch_id']}",
        ):
            res_rep = client.get(report_route, headers=headers_admin_a)
            assert res_rep.status_code == 404, f"Expected 404 on report {report_route}, got {res_rep.status_code}"
            assert res_rep.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # 5. INTRA-TENANT branch access controls:
        # Cashier A attempting access to Tenant A's other branch (branch_a2) gets 403 BRANCH_ACCESS_REQUIRED
        cashier_a2_res = client.get(f"/api/v1/reservations/branch?branch_id={branch_a2_id}", headers=headers_cashier_a)
        assert cashier_a2_res.status_code == 403
        assert cashier_a2_res.json()["detail"]["code"] == "BRANCH_ACCESS_REQUIRED"

        cashier_a2_sale = client.post(
            "/api/v1/sales/physical",
            headers=headers_cashier_a,
            json={"branch_id": branch_a2_id, "items": [{"product_variant_id": a["variant_id"], "quantity": 1}]},
        )
        assert cashier_a2_sale.status_code == 403
        assert cashier_a2_sale.json()["detail"]["code"] == "BRANCH_ACCESS_REQUIRED"

        # Company Admin of Tenant A has access to all branches of Tenant A
        admin_a2_inv = client.get(f"/api/v1/inventory?branch_id={branch_a2_id}", headers=headers_admin_a)
        assert admin_a2_inv.status_code == 200

        admin_a2_rep = client.get(f"/api/v1/reports/dashboard?branch_id={branch_a2_id}", headers=headers_admin_a)
        assert admin_a2_rep.status_code == 200
    finally:
        _restore_db_override(prev)


def test_t1_2_5_platform_endpoints_register_tenant_consult_plans_change_subscription_and_audit():
    from sqlalchemy import select
    from app.core.models import Permission, Role, RolePermission, SubscriptionPlan as AppPlan, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador de Plataforma SaaS")
            perms_platform = [
                Permission(code="saas.tenants.manage", name="Gestionar empresas"),
                Permission(code="saas.plans.manage", name="Gestionar planes"),
                Permission(code="saas.subscriptions.manage", name="Gestionar suscripciones"),
            ]
            db.add_all([role_admin, role_platform, *perms_platform])
            db.flush()
            for p in perms_platform:
                db.add(RolePermission(role_id=role_platform.id, permission_id=p.id))

            plan_basic = AppPlan(code="BASIC", name="Básico", max_active_branches=2, generative_reports_enabled=False, is_active=True)
            plan_pro = AppPlan(code="PROFESSIONAL", name="Profesional", max_active_branches=10, generative_reports_enabled=True, is_active=True)
            db.add_all([plan_basic, plan_pro])

            platform_admin = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Root",
                last_name="Platform",
                email="root@fashionstore.platform",
                phone="70009999",
                password_hash=hash_password("PlatformRoot123!"),
            )
            db.add(platform_admin)
            db.commit()

        login_res = client.post("/api/v1/auth/login", json={"email": "root@fashionstore.platform", "password": "PlatformRoot123!"})
        assert login_res.status_code == 200
        headers_platform = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # 1. Consult plans
        res_public_plans = client.get("/api/v1/plans")
        assert res_public_plans.status_code == 200
        plan_codes = [p["code"] for p in res_public_plans.json()["items"]]
        assert "BASIC" in plan_codes and "PROFESSIONAL" in plan_codes

        res_plat_plans = client.get("/api/v1/platform/plans", headers=headers_platform)
        assert res_plat_plans.status_code == 200
        assert len(res_plat_plans.json()["items"]) >= 2

        # 2. Register company (tenant) with initial admin and subscription
        create_res = client.post(
            "/api/v1/platform/tenants",
            headers=headers_platform,
            json={
                "name": "Textiles del Valle",
                "plan_code": "BASIC",
                "admin_email": "admin@textilesvalle.com",
                "admin_password": "ValleAdmin123!",
                "admin_first_name": "Marcos",
                "admin_last_name": "Valle",
                "admin_phone": "70099881",
            },
        )
        assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
        tenant_data = create_res.json()
        assert tenant_data["name"] == "Textiles del Valle"
        assert tenant_data["status"] == "ACTIVE"
        assert tenant_data["active_subscription"]["plan"]["code"] == "BASIC"
        new_tenant_id = tenant_data["id"]

        # Verify newly created admin can log in
        valle_login = client.post("/api/v1/auth/login", json={"email": "admin@textilesvalle.com", "password": "ValleAdmin123!"})
        assert valle_login.status_code == 200
        assert valle_login.json()["user"]["tenant_id"] == new_tenant_id

        # 3. Change subscription of tenant to PROFESSIONAL
        sub_change = client.post(
            f"/api/v1/platform/tenants/{new_tenant_id}/subscriptions",
            headers=headers_platform,
            json={"plan_code": "PROFESSIONAL"},
        )
        assert sub_change.status_code == 201
        assert sub_change.json()["plan"]["code"] == "PROFESSIONAL"
        assert sub_change.json()["status"] == "ACTIVE"

        # 4. Consult subscription history for that tenant
        sub_history = client.get(f"/api/v1/platform/tenants/{new_tenant_id}/subscriptions", headers=headers_platform)
        assert sub_history.status_code == 200
        history_items = sub_history.json()["items"]
        assert len(history_items) == 2
        statuses = [(item["plan"]["code"], item["status"]) for item in history_items]
        assert ("BASIC", "CANCELLED") in statuses
        assert ("PROFESSIONAL", "ACTIVE") in statuses
    finally:
        _restore_db_override(prev)


def test_t1_2_5_tenant_consults_current_subscription_status_and_company_admin_is_blocked_from_platform_subscription_management():
    from datetime import UTC, datetime
    from app.core.models import Permission, Role, RolePermission, Subscription as AppSub, SubscriptionPlan as AppPlan, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador de Plataforma SaaS")
            perm_users = Permission(code="users.manage", name="Gestionar usuarios")
            perm_saas = Permission(code="saas.tenants.manage", name="Gestionar empresas")
            db.add_all([role_admin, role_platform, perm_users, perm_saas])
            db.flush()
            db.add(RolePermission(role_id=role_admin.id, permission_id=perm_users.id))
            db.add(RolePermission(role_id=role_platform.id, permission_id=perm_saas.id))

            plan_pro = AppPlan(code="PROFESSIONAL", name="Profesional", max_active_branches=10, generative_reports_enabled=True, is_active=True)
            db.add(plan_pro)
            db.flush()

            t1 = AppTenant(name="Solares Corp", status="ACTIVE")
            db.add(t1)
            db.flush()

            sub = AppSub(tenant=t1, plan=plan_pro, status="ACTIVE", valid_from=datetime.now(UTC))
            company_admin = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Carlos",
                last_name="Solares",
                email="admin@solares.com",
                phone="71100220",
                password_hash=hash_password("SolaresPass123!"),
            )
            platform_admin = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Root",
                last_name="Platform",
                email="root@platform.org",
                phone="70009999",
                password_hash=hash_password("PlatformRoot123!"),
            )
            db.add_all([sub, company_admin, platform_admin])
            db.commit()
            t1_id = t1.id

        login_admin = client.post("/api/v1/auth/login", json={"email": "admin@solares.com", "password": "SolaresPass123!"})
        assert login_admin.status_code == 200
        headers_admin = {"Authorization": f"Bearer {login_admin.json()['access_token']}"}

        login_platform = client.post("/api/v1/auth/login", json={"email": "root@platform.org", "password": "PlatformRoot123!"})
        assert login_platform.status_code == 200
        headers_platform = {"Authorization": f"Bearer {login_platform.json()['access_token']}"}

        # 1. Company admin consults current subscription status and validity
        res_current = client.get("/api/v1/subscriptions/current", headers=headers_admin)
        assert res_current.status_code == 200
        body = res_current.json()
        assert body["tenant_id"] == t1_id
        assert body["tenant_name"] == "Solares Corp"
        assert body["plan"]["code"] == "PROFESSIONAL"
        assert body["max_active_branches"] == 10
        assert body["generative_reports_enabled"] is True
        assert body["subscription"]["status"] == "ACTIVE"

        # 2. Company admin cannot access platform subscription management
        res_blocked_sub = client.post(f"/api/v1/platform/tenants/{t1_id}/subscriptions", headers=headers_admin, json={"plan_code": "BASIC"})
        assert res_blocked_sub.status_code == 403
        assert res_blocked_sub.json()["detail"]["code"] == "PLATFORM_ADMIN_REQUIRED"

        # 3. Platform admin cannot access tenant operational subscription route
        res_blocked_plat = client.get("/api/v1/subscriptions/current", headers=headers_platform)
        assert res_blocked_plat.status_code == 403
        assert res_blocked_plat.json()["detail"]["code"] in {"ADMIN_ROLE_REQUIRED", "TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN"}
    finally:
        _restore_db_override(prev)


def test_t1_2_6_branch_quota_limit_enforced_transactionally_and_subscription_upgrade_unlocks_more_branches():
    from datetime import UTC, datetime
    from app.core.models import Branch as AppBranch, City, Permission, Role, RolePermission, Subscription as AppSub, SubscriptionPlan as AppPlan, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador SaaS")
            perms_admin = [
                Permission(code="locations.manage", name="Gestionar sucursales"),
                Permission(code="users.manage", name="Gestionar usuarios"),
            ]
            perms_platform = [
                Permission(code="saas.subscriptions.manage", name="Gestionar suscripciones"),
            ]
            db.add_all([role_admin, role_platform, *perms_admin, *perms_platform])
            db.flush()
            for p in perms_admin:
                db.add(RolePermission(role_id=role_admin.id, permission_id=p.id))
            for p in perms_platform:
                db.add(RolePermission(role_id=role_platform.id, permission_id=p.id))

            plan_basic = AppPlan(code="BASIC", name="Básico", max_active_branches=2, generative_reports_enabled=False, is_active=True)
            plan_pro = AppPlan(code="PROFESSIONAL", name="Profesional", max_active_branches=10, generative_reports_enabled=True, is_active=True)
            city = City(name="Santa Cruz")
            db.add_all([plan_basic, plan_pro, city])
            db.flush()

            t1 = AppTenant(name="Empresa Cuota", status="ACTIVE")
            db.add(t1)
            db.flush()

            sub = AppSub(tenant=t1, plan=plan_basic, status="ACTIVE", valid_from=datetime.now(UTC))
            company_admin = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Admin",
                last_name="Cuota",
                email="admin@cuota.com",
                phone="71002233",
                password_hash=hash_password("CuotaAdmin123!"),
            )
            platform_admin = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Platform",
                last_name="SaaS",
                email="root@platform.org",
                phone="70009999",
                password_hash=hash_password("PlatformRoot123!"),
            )
            db.add_all([sub, company_admin, platform_admin])
            db.commit()
            city_id = city.id
            t1_id = t1.id

        admin_login = client.post("/api/v1/auth/login", json={"email": "admin@cuota.com", "password": "CuotaAdmin123!"})
        assert admin_login.status_code == 200
        headers_admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        plat_login = client.post("/api/v1/auth/login", json={"email": "root@platform.org", "password": "PlatformRoot123!"})
        assert plat_login.status_code == 200
        headers_plat = {"Authorization": f"Bearer {plat_login.json()['access_token']}"}

        # 1. Create Branch 1 (1 of 2) -> Succeeds
        b1_res = client.post(
            "/api/v1/branches",
            headers=headers_admin,
            json={"city_id": city_id, "name": "Sucursal Cuota Uno", "address": "Av. Uno", "phone": "71000001"},
        )
        assert b1_res.status_code == 201
        b1_id = b1_res.json()["id"]

        # 2. Create Branch 2 (2 of 2) -> Succeeds (Quota full for BASIC plan)
        b2_res = client.post(
            "/api/v1/branches",
            headers=headers_admin,
            json={"city_id": city_id, "name": "Sucursal Cuota Dos", "address": "Av. Dos", "phone": "71000002"},
        )
        assert b2_res.status_code == 201
        b2_id = b2_res.json()["id"]

        # 3. Attempt to create Branch 3 (exceeding limit of 2) -> Rejected with 409 BRANCH_LIMIT_EXCEEDED
        b3_res = client.post(
            "/api/v1/branches",
            headers=headers_admin,
            json={"city_id": city_id, "name": "Sucursal Cuota Tres", "address": "Av. Tres", "phone": "71000003"},
        )
        assert b3_res.status_code == 409
        assert b3_res.json()["detail"]["code"] == "BRANCH_LIMIT_EXCEEDED"

        # 4. Deactivate Branch 2 -> Active count drops from 2 to 1
        deact_res = client.patch(f"/api/v1/branches/{b2_id}/deactivate", headers=headers_admin)
        assert deact_res.status_code == 200
        assert deact_res.json()["is_active"] is False

        # Now creating Branch 3 succeeds because active branches = 1 < 2
        b3_ok_res = client.post(
            "/api/v1/branches",
            headers=headers_admin,
            json={"city_id": city_id, "name": "Sucursal Cuota Tres", "address": "Av. Tres", "phone": "71000003"},
        )
        assert b3_ok_res.status_code == 201
        b3_id = b3_ok_res.json()["id"]

        # Attempting to re-activate Branch 2 would exceed limit of 2 -> Rejected with 409
        react_res = client.patch(f"/api/v1/branches/{b2_id}/activate", headers=headers_admin)
        assert react_res.status_code == 409
        assert react_res.json()["detail"]["code"] == "BRANCH_LIMIT_EXCEEDED"

        # 5. Upgrade subscription from BASIC (2) to PROFESSIONAL (10)
        upgrade_res = client.post(
            f"/api/v1/platform/tenants/{t1_id}/subscriptions",
            headers=headers_plat,
            json={"plan_code": "PROFESSIONAL"},
        )
        assert upgrade_res.status_code == 201

        # Now re-activating Branch 2 succeeds!
        react_ok = client.patch(f"/api/v1/branches/{b2_id}/activate", headers=headers_admin)
        assert react_ok.status_code == 200
        assert react_ok.json()["is_active"] is True

        # And creating Branch 4 also succeeds!
        b4_res = client.post(
            "/api/v1/branches",
            headers=headers_admin,
            json={"city_id": city_id, "name": "Sucursal Cuota Cuatro", "address": "Av. Cuatro", "phone": "71000004"},
        )
        assert b4_res.status_code == 201
    finally:
        _restore_db_override(prev)


def test_t1_2_6_feature_flag_generative_reports_enforced_by_plan():
    from datetime import UTC, datetime
    from app.core.models import Permission, Role, RolePermission, Subscription as AppSub, SubscriptionPlan as AppPlan, Tenant as AppTenant, User as AppUser
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador SaaS")
            perm_reports = Permission(code="reports.read", name="Consultar reportes")
            perm_subs = Permission(code="saas.subscriptions.manage", name="Gestionar suscripciones")
            db.add_all([role_admin, role_platform, perm_reports, perm_subs])
            db.flush()
            db.add(RolePermission(role_id=role_admin.id, permission_id=perm_reports.id))
            db.add(RolePermission(role_id=role_platform.id, permission_id=perm_subs.id))

            plan_basic = AppPlan(code="BASIC", name="Básico", max_active_branches=2, generative_reports_enabled=False, is_active=True)
            plan_pro = AppPlan(code="PROFESSIONAL", name="Profesional", max_active_branches=10, generative_reports_enabled=True, is_active=True)
            db.add_all([plan_basic, plan_pro])

            t1 = AppTenant(name="Empresa Feature", status="ACTIVE")
            db.add(t1)
            db.flush()

            sub = AppSub(tenant=t1, plan=plan_basic, status="ACTIVE", valid_from=datetime.now(UTC))
            company_admin = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Admin",
                last_name="Feature",
                email="admin@feature.com",
                phone="71004455",
                password_hash=hash_password("FeatureAdmin123!"),
            )
            platform_admin = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Platform",
                last_name="SaaS",
                email="root@platform.org",
                phone="70009999",
                password_hash=hash_password("PlatformRoot123!"),
            )
            db.add_all([sub, company_admin, platform_admin])
            db.commit()
            t1_id = t1.id

        admin_login = client.post("/api/v1/auth/login", json={"email": "admin@feature.com", "password": "FeatureAdmin123!"})
        assert admin_login.status_code == 200
        headers_admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        plat_login = client.post("/api/v1/auth/login", json={"email": "root@platform.org", "password": "PlatformRoot123!"})
        assert plat_login.status_code == 200
        headers_plat = {"Authorization": f"Bearer {plat_login.json()['access_token']}"}

        # 1. On BASIC plan (generative_reports_enabled=False), POST /api/v1/reports/assistant is blocked with 403 FEATURE_NOT_IN_PLAN
        res_blocked_ai = client.post(
            "/api/v1/reports/assistant",
            headers=headers_admin,
            json={"prompt": "¿Cuáles son las ventas por sucursal?"},
        )
        assert res_blocked_ai.status_code == 403
        assert res_blocked_ai.json()["detail"]["code"] == "FEATURE_NOT_IN_PLAN"

        # Standard dashboard reports are NOT blocked
        res_dash = client.get("/api/v1/reports/dashboard", headers=headers_admin)
        assert res_dash.status_code == 200

        # 2. Upgrade plan to PROFESSIONAL (generative_reports_enabled=True)
        upgrade_res = client.post(
            f"/api/v1/platform/tenants/{t1_id}/subscriptions",
            headers=headers_plat,
            json={"plan_code": "PROFESSIONAL"},
        )
        assert upgrade_res.status_code == 201

        # 3. On PROFESSIONAL plan, POST /api/v1/reports/assistant is allowed!
        res_allowed_ai = client.post(
            "/api/v1/reports/assistant",
            headers=headers_admin,
            json={"prompt": "¿Cuáles son las ventas por sucursal?"},
        )
        assert res_allowed_ai.status_code == 200
        assert "intent" in res_allowed_ai.json()
    finally:
        _restore_db_override(prev)


def test_t1_2_7_sync_catalog_derived_and_validated_with_offline_metadata_and_isolation():
    from datetime import UTC, datetime
    from decimal import Decimal
    from app.core.models import (
        Branch,
        Category,
        City,
        Color,
        Inventory,
        Permission,
        Product,
        ProductVariant,
        Role,
        RolePermission,
        Size,
        Subscription as AppSub,
        SubscriptionPlan as AppPlan,
        Tenant as AppTenant,
        User as AppUser,
    )
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_cashier = Role(code="CASHIER", name="Cajero")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador SaaS")
            perm_cat = Permission(code="catalog.read", name="Consultar catálogo")
            perm_sales = Permission(code="sales.create", name="Registrar ventas")
            perm_plat = Permission(code="saas.tenants.manage", name="Gestionar empresas")
            db.add_all([role_admin, role_cashier, role_platform, perm_cat, perm_sales, perm_plat])
            db.flush()
            db.add_all([
                RolePermission(role_id=role_admin.id, permission_id=perm_cat.id),
                RolePermission(role_id=role_cashier.id, permission_id=perm_cat.id),
                RolePermission(role_id=role_cashier.id, permission_id=perm_sales.id),
                RolePermission(role_id=role_platform.id, permission_id=perm_plat.id),
            ])

            plan = AppPlan(code="BASIC", name="Básico", max_active_branches=5, generative_reports_enabled=False, is_active=True)
            city = City(name="Santa Cruz")
            size_m = Size(name="M", sort_order=1)
            size_l = Size(name="L", sort_order=2)
            color_blue = Color(name="Azul", hex_code="#0000FF")
            db.add_all([plan, city, size_m, size_l, color_blue])
            db.flush()

            # Tenant 1
            t1 = AppTenant(name="Empresa Uno", status="ACTIVE")
            db.add(t1)
            db.flush()
            sub1 = AppSub(tenant=t1, plan=plan, status="ACTIVE", valid_from=datetime.now(UTC))
            b1a = Branch(tenant=t1, city=city, name="Sucursal 1A", address="Av. 1A", phone="71000001", is_active=True)
            b1b = Branch(tenant=t1, city=city, name="Sucursal 1B", address="Av. 1B", phone="71000002", is_active=True)
            db.add_all([sub1, b1a, b1b])
            db.flush()

            admin1 = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Admin",
                last_name="Uno",
                email="admin1@empresa.com",
                phone="71001111",
                password_hash=hash_password("AdminPass123!"),
            )
            cashier1 = AppUser(
                tenant=t1,
                role=role_cashier,
                first_name="Cajera",
                last_name="Uno",
                email="cajera1@empresa.com",
                phone="71001112",
                password_hash=hash_password("CashierPass123!"),
                branches=[b1a],  # Assigned only to 1A
            )
            db.add_all([admin1, cashier1])

            cat1 = Category(tenant=t1, name="Camisas", is_active=True)
            db.add(cat1)
            db.flush()

            prod1 = Product(
                tenant=t1,
                category=cat1,
                name="Camisa Lino",
                code="CAM-01",
                slug="camisa-lino",
                description="Camisa fresca de lino",
                price=Decimal("150.00"),
                is_active=True,
            )
            db.add(prod1)
            db.flush()

            var1a = ProductVariant(tenant=t1, product=prod1, size=size_m, color=color_blue, sku="CAM-01-M-BLU", is_active=True)
            var1b = ProductVariant(tenant=t1, product=prod1, size=size_l, color=color_blue, sku="CAM-01-L-BLU", is_active=True)
            db.add_all([var1a, var1b])
            db.flush()

            inv1a_m = Inventory(tenant=t1, branch=b1a, product_variant=var1a, stock_quantity=10, reserved_quantity=2)
            inv1a_l = Inventory(tenant=t1, branch=b1a, product_variant=var1b, stock_quantity=5, reserved_quantity=0)
            inv1b_m = Inventory(tenant=t1, branch=b1b, product_variant=var1a, stock_quantity=20, reserved_quantity=5)
            db.add_all([inv1a_m, inv1a_l, inv1b_m])

            # Tenant 2 (For cross-tenant isolation testing)
            t2 = AppTenant(name="Empresa Dos", status="ACTIVE")
            db.add(t2)
            db.flush()
            sub2 = AppSub(tenant=t2, plan=plan, status="ACTIVE", valid_from=datetime.now(UTC))
            b2a = Branch(tenant=t2, city=city, name="Sucursal 2A", address="Av. 2A", phone="72000001", is_active=True)
            db.add_all([sub2, b2a])
            db.flush()

            admin2 = AppUser(
                tenant=t2,
                role=role_admin,
                first_name="Admin",
                last_name="Dos",
                email="admin2@empresa.com",
                phone="72001111",
                password_hash=hash_password("Admin2Pass123!"),
            )
            cat2 = Category(tenant=t2, name="Pantalones", is_active=True)
            db.add_all([admin2, cat2])
            db.flush()

            prod2 = Product(
                tenant=t2,
                category=cat2,
                name="Jean Clasico",
                code="JEA-01",
                slug="jean-clasico",
                description="Jean azul clasico",
                price=Decimal("220.00"),
                is_active=True,
            )
            db.add(prod2)
            db.flush()

            var2a = ProductVariant(tenant=t2, product=prod2, size=size_m, color=color_blue, sku="JEA-01-M-BLU", is_active=True)
            db.add(var2a)
            db.flush()
            inv2a = Inventory(tenant=t2, branch=b2a, product_variant=var2a, stock_quantity=50, reserved_quantity=0)
            db.add(inv2a)

            # Platform Admin
            platform_user = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Plat",
                last_name="Admin",
                email="platform@saas.com",
                phone="70009999",
                password_hash=hash_password("PlatPass123!"),
            )
            db.add(platform_user)
            db.commit()

            t1_id = t1.id
            b1a_id = b1a.id
            b1b_id = b1b.id
            b2a_id = b2a.id
            var1a_id = var1a.id
            var1b_id = var1b.id

        # Logins
        login_c1 = client.post("/api/v1/auth/login", json={"email": "cajera1@empresa.com", "password": "CashierPass123!"})
        assert login_c1.status_code == 200
        headers_c1 = {"Authorization": f"Bearer {login_c1.json()['access_token']}"}

        login_a1 = client.post("/api/v1/auth/login", json={"email": "admin1@empresa.com", "password": "AdminPass123!"})
        assert login_a1.status_code == 200
        headers_a1 = {"Authorization": f"Bearer {login_a1.json()['access_token']}"}

        login_plat = client.post("/api/v1/auth/login", json={"email": "platform@saas.com", "password": "PlatPass123!"})
        assert login_plat.status_code == 200
        headers_plat = {"Authorization": f"Bearer {login_plat.json()['access_token']}"}

        # 1. Cashier 1 derives assigned branch (1A) automatically without branch_id parameter
        res_sync_c1 = client.get("/api/v1/sync/catalog", headers=headers_c1)
        assert res_sync_c1.status_code == 200, res_sync_c1.text
        data_c1 = res_sync_c1.json()

        # Metadata validation
        assert data_c1["metadata"]["tenant_id"] == t1_id
        assert data_c1["metadata"]["tenant_name"] == "Empresa Uno"
        assert data_c1["metadata"]["branch_id"] == b1a_id
        assert data_c1["metadata"]["branch_name"] == "Sucursal 1A"
        assert "catalog_version" in data_c1["metadata"]
        assert "sync_timestamp" in data_c1["metadata"]

        # Categories: only Tenant 1
        cat_names = [c["name"] for c in data_c1["categories"]]
        assert "Camisas" in cat_names
        assert "Pantalones" not in cat_names

        # Products: only Tenant 1
        prod_codes = [p["code"] for p in data_c1["products"]]
        assert "CAM-01" in prod_codes
        assert "JEA-01" not in prod_codes

        # Variants: only Tenant 1
        var_skus = [v["sku"] for v in data_c1["variants"]]
        assert "CAM-01-M-BLU" in var_skus
        assert "CAM-01-L-BLU" in var_skus
        assert "JEA-01-M-BLU" not in var_skus

        # Local Branch Inventory: only Branch 1A stock
        inv_map = {item["product_variant_id"]: item for item in data_c1["inventory"]}
        assert var1a_id in inv_map
        assert inv_map[var1a_id]["stock_quantity"] == 10
        assert inv_map[var1a_id]["reserved_quantity"] == 2
        assert inv_map[var1a_id]["available_quantity"] == 8

        assert var1b_id in inv_map
        assert inv_map[var1b_id]["stock_quantity"] == 5
        assert inv_map[var1b_id]["reserved_quantity"] == 0
        assert inv_map[var1b_id]["available_quantity"] == 5

        # 2. Cashier 1 tries to sync Branch 1B (unassigned branch within same tenant) -> 403 BRANCH_ACCESS_REQUIRED
        res_c1_b1b = client.get(f"/api/v1/sync/catalog?branch_id={b1b_id}", headers=headers_c1)
        assert res_c1_b1b.status_code == 403
        assert res_c1_b1b.json()["detail"]["code"] == "BRANCH_ACCESS_REQUIRED"

        # 3. Cashier 1 tries to sync Branch 2A from another tenant -> 404 non-enumerable BRANCH_NOT_FOUND
        res_c1_b2a = client.get(f"/api/v1/sync/catalog?branch_id={b2a_id}", headers=headers_c1)
        assert res_c1_b2a.status_code == 404
        assert res_c1_b2a.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # 4. Admin 1 syncs Branch 1B explicitly -> succeeds with Branch 1B inventory
        res_admin_b1b = client.get(f"/api/v1/sync/catalog?branch_id={b1b_id}", headers=headers_a1)
        assert res_admin_b1b.status_code == 200
        data_a1_b1b = res_admin_b1b.json()
        assert data_a1_b1b["metadata"]["branch_id"] == b1b_id
        assert data_a1_b1b["metadata"]["branch_name"] == "Sucursal 1B"
        inv_b1b_map = {item["product_variant_id"]: item for item in data_a1_b1b["inventory"]}
        assert inv_b1b_map[var1a_id]["stock_quantity"] == 20
        assert inv_b1b_map[var1a_id]["reserved_quantity"] == 5
        assert inv_b1b_map[var1a_id]["available_quantity"] == 15

        # 5. Admin 1 tries to sync Branch 2A from another tenant -> 404 non-enumerable BRANCH_NOT_FOUND
        res_admin_b2a = client.get(f"/api/v1/sync/catalog?branch_id={b2a_id}", headers=headers_a1)
        assert res_admin_b2a.status_code == 404
        assert res_admin_b2a.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # 6. Platform Admin is blocked from syncing tenant catalog -> 403 TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN
        res_plat = client.get("/api/v1/sync/catalog", headers=headers_plat)
        assert res_plat.status_code == 403
        assert res_plat.json()["detail"]["code"] == "TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN"
    finally:
        _restore_db_override(prev)


def test_t1_2_8_multi_tenant_isolation_reads_mutations_alien_branches_and_platform_perms():
    from datetime import UTC, datetime
    from decimal import Decimal
    from app.core.models import (
        Branch,
        Category,
        City,
        Color,
        Inventory,
        Permission,
        Product,
        ProductVariant,
        Role,
        RolePermission,
        Size,
        Subscription as AppSub,
        SubscriptionPlan as AppPlan,
        Tenant as AppTenant,
        User as AppUser,
    )
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_platform = Role(code="PLATFORM_ADMIN", name="Administrador SaaS")
            perms_tenant = [
                Permission(code="catalog.read", name="Consultar catálogo"),
                Permission(code="products.manage", name="Gestionar productos"),
                Permission(code="masters.manage", name="Gestionar maestros"),
                Permission(code="locations.manage", name="Gestionar sucursales"),
                Permission(code="inventory.read", name="Consultar inventario"),
                Permission(code="reservations.manage", name="Gestionar reservas"),
                Permission(code="reservations.create", name="Crear reservas"),
                Permission(code="sales.create", name="Registrar ventas"),
                Permission(code="reports.read", name="Consultar reportes"),
            ]
            perms_platform = [
                Permission(code="saas.tenants.manage", name="Gestionar empresas"),
                Permission(code="saas.plans.manage", name="Gestionar planes"),
                Permission(code="saas.subscriptions.manage", name="Gestionar suscripciones"),
            ]
            db.add_all([role_admin, role_platform, *perms_tenant, *perms_platform])
            db.flush()
            for p in perms_tenant:
                db.add(RolePermission(role_id=role_admin.id, permission_id=p.id))
            for p in perms_platform:
                db.add(RolePermission(role_id=role_platform.id, permission_id=p.id))

            plan_basic = AppPlan(code="BASIC", name="Básico", max_active_branches=2, generative_reports_enabled=False, is_active=True)
            plan_pro = AppPlan(code="PROFESSIONAL", name="Profesional", max_active_branches=10, generative_reports_enabled=True, is_active=True)
            city = City(name="Santa Cruz")
            size_m = Size(name="M", sort_order=1)
            color_blue = Color(name="Azul", hex_code="#0000FF")
            db.add_all([plan_basic, plan_pro, city, size_m, color_blue])
            db.flush()

            # Tenant 1 (Alpha)
            t1 = AppTenant(name="Empresa Alpha", status="ACTIVE")
            db.add(t1)
            db.flush()
            sub1 = AppSub(tenant=t1, plan=plan_basic, status="ACTIVE", valid_from=datetime.now(UTC))
            b1a = Branch(tenant=t1, city=city, name="Alpha Central", address="Av. Central 1", phone="71110001", is_active=True)
            b1b = Branch(tenant=t1, city=city, name="Alpha Norte", address="Av. Norte 1", phone="71110002", is_active=True)
            admin1 = AppUser(
                tenant=t1,
                role=role_admin,
                first_name="Admin",
                last_name="Alpha",
                email="admin@alpha.com",
                phone="71110010",
                password_hash=hash_password("AlphaAdmin123!"),
            )
            cat1 = Category(tenant=t1, name="Ropa Alpha", is_active=True)
            db.add_all([sub1, b1a, b1b, admin1, cat1])
            db.flush()

            prod1 = Product(tenant=t1, category=cat1, name="Camisa Alpha", code="ALP-001", slug="camisa-alpha", price=Decimal("100.00"), is_active=True)
            db.add(prod1)
            db.flush()

            var1 = ProductVariant(tenant=t1, product=prod1, size=size_m, color=color_blue, sku="ALP-001-M", is_active=True)
            db.add(var1)
            db.flush()
            inv1 = Inventory(tenant=t1, branch=b1a, product_variant=var1, stock_quantity=50, reserved_quantity=0)
            db.add(inv1)

            # Tenant 2 (Beta)
            t2 = AppTenant(name="Empresa Beta", status="ACTIVE")
            db.add(t2)
            db.flush()
            sub2 = AppSub(tenant=t2, plan=plan_pro, status="ACTIVE", valid_from=datetime.now(UTC))
            b2a = Branch(tenant=t2, city=city, name="Beta Sur", address="Av. Sur 2", phone="72220001", is_active=True)
            admin2 = AppUser(
                tenant=t2,
                role=role_admin,
                first_name="Admin",
                last_name="Beta",
                email="admin@beta.com",
                phone="72220010",
                password_hash=hash_password("BetaAdmin123!"),
            )
            cat2 = Category(tenant=t2, name="Ropa Beta", is_active=True)
            db.add_all([sub2, b2a, admin2, cat2])
            db.flush()

            prod2 = Product(tenant=t2, category=cat2, name="Pantalon Beta", code="BET-001", slug="pantalon-beta", price=Decimal("200.00"), is_active=True)
            db.add(prod2)
            db.flush()

            var2 = ProductVariant(tenant=t2, product=prod2, size=size_m, color=color_blue, sku="BET-001-M", is_active=True)
            db.add(var2)
            db.flush()
            inv2 = Inventory(tenant=t2, branch=b2a, product_variant=var2, stock_quantity=30, reserved_quantity=0)
            db.add(inv2)

            # Platform Admin
            platform_user = AppUser(
                tenant=None,
                role=role_platform,
                first_name="Platform",
                last_name="SaaS",
                email="root@saas.com",
                phone="70009999",
                password_hash=hash_password("PlatformRoot123!"),
            )
            db.add(platform_user)
            db.commit()

            t1_id = t1.id
            b1a_id = b1a.id
            b1b_id = b1b.id
            cat1_id = cat1.id
            prod1_id = prod1.id
            var1_id = var1.id

            t2_id = t2.id
            b2a_id = b2a.id
            cat2_id = cat2.id
            prod2_id = prod2.id
            var2_id = var2.id
            city_id = city.id

        # Logins
        login_a1 = client.post("/api/v1/auth/login", json={"email": "admin@alpha.com", "password": "AlphaAdmin123!"})
        assert login_a1.status_code == 200
        headers_a1 = {"Authorization": f"Bearer {login_a1.json()['access_token']}"}

        login_plat = client.post("/api/v1/auth/login", json={"email": "root@saas.com", "password": "PlatformRoot123!"})
        assert login_plat.status_code == 200
        headers_plat = {"Authorization": f"Bearer {login_plat.json()['access_token']}"}

        # -------------------------------------------------------------
        # 1. Cross-tenant reading & mutation isolation
        # -------------------------------------------------------------
        # Listing products lists only Alpha's products
        res_prods = client.get("/api/v1/products", headers=headers_a1)
        assert res_prods.status_code == 200
        prod_codes = [p["code"] for p in res_prods.json()["items"]]
        assert "ALP-001" in prod_codes
        assert "BET-001" not in prod_codes

        # Attempting to read Beta's product returns 404 (non-enumerable)
        res_read_alien_prod = client.get(f"/api/v1/products/{prod2_id}", headers=headers_a1)
        assert res_read_alien_prod.status_code == 404

        # Attempting to mutate Beta's product returns 404
        res_patch_alien_prod = client.patch(
            f"/api/v1/products/{prod2_id}",
            headers=headers_a1,
            json={"name": "Camisa Modificada Ilegitima"},
        )
        assert res_patch_alien_prod.status_code == 404

        # Listing categories lists only Alpha's categories
        res_cats = client.get("/api/v1/categories", headers=headers_a1)
        assert res_cats.status_code == 200
        cat_names = [c["name"] for c in res_cats.json()["items"]]
        assert "Ropa Alpha" in cat_names
        assert "Ropa Beta" not in cat_names

        # Attempting to read/mutate Beta's category returns 404
        assert client.get(f"/api/v1/categories/{cat2_id}", headers=headers_a1).status_code == 404
        assert client.patch(f"/api/v1/categories/{cat2_id}", headers=headers_a1, json={"name": "Hacked"}).status_code == 404

        # Listing branches lists only Alpha's branches
        res_branches = client.get("/api/v1/branches", headers=headers_a1)
        assert res_branches.status_code == 200
        branch_ids = [b["id"] for b in res_branches.json()["items"]]
        assert b1a_id in branch_ids
        assert b1b_id in branch_ids
        assert b2a_id not in branch_ids

        # Attempting to read/mutate/deactivate Beta's branch returns 404
        assert client.get(f"/api/v1/branches/{b2a_id}", headers=headers_a1).status_code == 404
        assert client.patch(f"/api/v1/branches/{b2a_id}", headers=headers_a1, json={"name": "Hacked"}).status_code == 404
        assert client.patch(f"/api/v1/branches/{b2a_id}/deactivate", headers=headers_a1).status_code == 404

        # -------------------------------------------------------------
        # 2. Alien branch access across operations returns 404/400
        # -------------------------------------------------------------
        # Inventory
        res_inv_alien = client.get(f"/api/v1/inventory?branch_id={b2a_id}", headers=headers_a1)
        assert res_inv_alien.status_code == 404
        assert res_inv_alien.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # Sync catalog
        res_sync_alien = client.get(f"/api/v1/sync/catalog?branch_id={b2a_id}", headers=headers_a1)
        assert res_sync_alien.status_code == 404
        assert res_sync_alien.json()["detail"]["code"] == "BRANCH_NOT_FOUND"

        # Commerce digital purchase with alien branch
        res_sale_alien = client.post(
            "/api/v1/commerce/digital-purchase",
            headers=headers_a1,
            json={
                "pickup_branch_id": b2a_id,
                "lines": [{"product_variant_id": var1_id, "quantity": 1}],
                "idempotency_key": "test-idem-alien-01",
            },
        )
        assert res_sale_alien.status_code in (400, 404)

        # Reservations with alien branch
        res_res_alien = client.post(
            "/api/v1/reservations",
            headers=headers_a1,
            json={
                "branch_id": b2a_id,
                "items": [{"product_variant_id": var1_id, "quantity": 1}],
            },
        )
        assert res_res_alien.status_code == 400
        assert res_res_alien.json()["detail"]["code"] == "BRANCH_NOT_FOUND_OR_INACTIVE"

        # -------------------------------------------------------------
        # 3. SaaS platform administration vs Tenant administration
        # -------------------------------------------------------------
        # Tenant admin cannot access platform endpoints
        assert client.get("/api/v1/platform/tenants", headers=headers_a1).status_code == 403
        assert client.get("/api/v1/platform/plans", headers=headers_a1).status_code == 403
        assert client.post(f"/api/v1/platform/tenants/{t1_id}/subscriptions", headers=headers_a1, json={"plan_code": "PROFESSIONAL"}).status_code == 403

        # Platform admin cannot access tenant-owned operational endpoints
        assert client.get("/api/v1/products", headers=headers_plat).status_code == 403
        assert client.get("/api/v1/sync/catalog", headers=headers_plat).status_code == 403
        assert client.get("/api/v1/reports/dashboard", headers=headers_plat).status_code == 403

        # -------------------------------------------------------------
        # 4. Plan quotas & limits: branch limit and feature flags
        # -------------------------------------------------------------
        # Alpha is on BASIC (limit: 2 branches). Currently has 2 active branches.
        res_limit_b3 = client.post(
            "/api/v1/branches",
            headers=headers_a1,
            json={"city_id": city_id, "name": "Alpha Sur", "address": "Av. Sur", "phone": "71110003"},
        )
        assert res_limit_b3.status_code == 409
        assert res_limit_b3.json()["detail"]["code"] == "BRANCH_LIMIT_EXCEEDED"

        # AI report assistant blocked by feature flag on BASIC
        res_ai_blocked = client.post(
            "/api/v1/reports/assistant",
            headers=headers_a1,
            json={"prompt": "Ventas del mes"},
        )
        assert res_ai_blocked.status_code == 403
        assert res_ai_blocked.json()["detail"]["code"] == "FEATURE_NOT_IN_PLAN"

        # Platform Admin upgrades Alpha to PROFESSIONAL
        res_upgrade = client.post(
            f"/api/v1/platform/tenants/{t1_id}/subscriptions",
            headers=headers_plat,
            json={"plan_code": "PROFESSIONAL"},
        )
        assert res_upgrade.status_code == 201

        # Now creating 3rd branch succeeds
        res_b3_ok = client.post(
            "/api/v1/branches",
            headers=headers_a1,
            json={"city_id": city_id, "name": "Alpha Sur", "address": "Av. Sur", "phone": "71110003"},
        )
        assert res_b3_ok.status_code == 201

        # Now AI report assistant succeeds
        res_ai_ok = client.post(
            "/api/v1/reports/assistant",
            headers=headers_a1,
            json={"prompt": "Ventas del mes"},
        )
        assert res_ai_ok.status_code == 200
        assert "intent" in res_ai_ok.json()
    finally:
        _restore_db_override(prev)


def test_t1_2_9_sync_catalog_filtering_by_tenant_and_branch_and_absence_of_other_tenant_info():
    from datetime import UTC, datetime
    from decimal import Decimal
    from app.core.models import (
        Branch,
        Category,
        City,
        Color,
        Inventory,
        Permission,
        Product,
        ProductVariant,
        Role,
        RolePermission,
        Size,
        Subscription as AppSub,
        SubscriptionPlan as AppPlan,
        Tenant as AppTenant,
        User as AppUser,
    )
    from app.core.security import hash_password

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            role_admin = Role(code="ADMIN", name="Administrador")
            role_cashier = Role(code="CASHIER", name="Cajero")
            perm_cat = Permission(code="catalog.read", name="Consultar catálogo")
            db.add_all([role_admin, role_cashier, perm_cat])
            db.flush()
            db.add_all([
                RolePermission(role_id=role_admin.id, permission_id=perm_cat.id),
                RolePermission(role_id=role_cashier.id, permission_id=perm_cat.id),
            ])

            plan = AppPlan(code="BASIC", name="Básico", max_active_branches=5, generative_reports_enabled=False, is_active=True)
            city = City(name="Santa Cruz")
            size_s = Size(name="S", size_type="NUMERIC", sort_order=7)
            size_m = Size(name="M", size_type="ALPHA", sort_order=2)
            color_red = Color(name="Rojo", hex_code="#FF0000")
            db.add_all([plan, city, size_s, size_m, color_red])
            db.flush()

            # Tenant X
            tx = AppTenant(name="Empresa X", status="ACTIVE")
            db.add(tx)
            db.flush()
            sub_x = AppSub(tenant=tx, plan=plan, status="ACTIVE", valid_from=datetime.now(UTC))
            bx1 = Branch(tenant=tx, city=city, name="Sucursal X-Principal", address="Calle X 1", phone="73330001", is_active=True)
            bx2 = Branch(tenant=tx, city=city, name="Sucursal X-Secundaria", address="Calle X 2", phone="73330002", is_active=True)
            admin_x = AppUser(
                tenant=tx,
                role=role_admin,
                first_name="Admin",
                last_name="X",
                email="admin@empresax.com",
                phone="73330010",
                password_hash=hash_password("PassX123!"),
            )
            cat_x = Category(tenant=tx, name="Categoria X Exclusiva", is_active=True)
            db.add_all([sub_x, bx1, bx2, admin_x, cat_x])
            db.flush()

            prod_x = Product(tenant=tx, category=cat_x, name="Producto X", code="PROD-X-99", slug="producto-x", price=Decimal("88.00"), audience="MEN", size_system="NUMERIC", is_active=True)
            db.add(prod_x)
            db.flush()

            var_x = ProductVariant(tenant=tx, product=prod_x, size=size_s, color=color_red, sku="SKU-X-99", is_active=True)
            inactive_var_x = ProductVariant(tenant=tx, product=prod_x, size=size_m, color=color_red, sku="SKU-X-INACTIVE", is_active=False)
            db.add_all([var_x, inactive_var_x])
            db.flush()

            inv_x1 = Inventory(tenant=tx, branch=bx1, product_variant=var_x, stock_quantity=40, reserved_quantity=5)
            inv_x2 = Inventory(tenant=tx, branch=bx2, product_variant=var_x, stock_quantity=15, reserved_quantity=2)
            db.add_all([inv_x1, inv_x2])

            # Tenant Y (Must NEVER appear in Tenant X's sync response)
            ty = AppTenant(name="Empresa Y", status="ACTIVE")
            db.add(ty)
            db.flush()
            sub_y = AppSub(tenant=ty, plan=plan, status="ACTIVE", valid_from=datetime.now(UTC))
            by1 = Branch(tenant=ty, city=city, name="Sucursal Y-Aislada", address="Calle Y 1", phone="74440001", is_active=True)
            admin_y = AppUser(
                tenant=ty,
                role=role_admin,
                first_name="Admin",
                last_name="Y",
                email="admin@empresay.com",
                phone="74440010",
                password_hash=hash_password("PassY123!"),
            )
            cat_y = Category(tenant=ty, name="Categoria Y Secreta", is_active=True)
            db.add_all([sub_y, by1, admin_y, cat_y])
            db.flush()

            prod_y = Product(tenant=ty, category=cat_y, name="Producto Y Secreto", code="PROD-Y-SECRET", slug="producto-y", price=Decimal("999.00"), is_active=True)
            db.add(prod_y)
            db.flush()

            var_y = ProductVariant(tenant=ty, product=prod_y, size=size_s, color=color_red, sku="SKU-Y-SECRET", is_active=True)
            db.add(var_y)
            db.flush()

            inv_y = Inventory(tenant=ty, branch=by1, product_variant=var_y, stock_quantity=100, reserved_quantity=0)
            db.add(inv_y)
            db.commit()

            tx_id = tx.id
            bx1_id = bx1.id
            bx2_id = bx2.id
            var_x_id = var_x.id

            ty_id = ty.id
            by1_id = by1.id
            var_y_id = var_y.id

        # Admin X Login
        login_x = client.post("/api/v1/auth/login", json={"email": "admin@empresax.com", "password": "PassX123!"})
        assert login_x.status_code == 200
        headers_x = {"Authorization": f"Bearer {login_x.json()['access_token']}"}

        # 1. Sync for Sucursal X-Principal
        res_sync_x1 = client.get(f"/api/v1/sync/catalog?branch_id={bx1_id}", headers=headers_x)
        assert res_sync_x1.status_code == 200
        data_x1 = res_sync_x1.json()

        # Metadata
        assert data_x1["metadata"]["tenant_id"] == tx_id
        assert data_x1["metadata"]["tenant_name"] == "Empresa X"
        assert data_x1["metadata"]["branch_id"] == bx1_id
        assert data_x1["metadata"]["branch_name"] == "Sucursal X-Principal"

        # Categories: Categoria X present, Categoria Y absent
        cat_names = [c["name"] for c in data_x1["categories"]]
        assert "Categoria X Exclusiva" in cat_names
        assert "Categoria Y Secreta" not in cat_names

        # Products: Producto X present, Producto Y absent
        prod_codes = [p["code"] for p in data_x1["products"]]
        assert "PROD-X-99" in prod_codes
        assert "PROD-Y-SECRET" not in prod_codes

        # Variants: active SKU-X present, inactive and alien variants absent
        var_skus = [v["sku"] for v in data_x1["variants"]]
        assert "SKU-X-99" in var_skus
        assert "SKU-X-INACTIVE" not in var_skus
        assert "SKU-Y-SECRET" not in var_skus
        product_x_payload = next(p for p in data_x1["products"] if p["code"] == "PROD-X-99")
        assert product_x_payload["audience"] == "MEN"
        assert product_x_payload["size_system"] == "NUMERIC"
        variant_x_payload = next(v for v in data_x1["variants"] if v["sku"] == "SKU-X-99")
        assert variant_x_payload["size_type"] == "NUMERIC"
        assert variant_x_payload["sort_order"] == 7

        # Inventory for Sucursal X1: only X1 stock (40-5=35)
        inv_x1_map = {item["product_variant_id"]: item for item in data_x1["inventory"]}
        assert var_x_id in inv_x1_map
        assert inv_x1_map[var_x_id]["stock_quantity"] == 40
        assert inv_x1_map[var_x_id]["reserved_quantity"] == 5
        assert inv_x1_map[var_x_id]["available_quantity"] == 35
        # Must not contain var_y
        assert var_y_id not in inv_x1_map

        # 2. Sync for Sucursal X-Secundaria
        res_sync_x2 = client.get(f"/api/v1/sync/catalog?branch_id={bx2_id}", headers=headers_x)
        assert res_sync_x2.status_code == 200
        data_x2 = res_sync_x2.json()
        assert data_x2["metadata"]["branch_id"] == bx2_id
        assert data_x2["metadata"]["branch_name"] == "Sucursal X-Secundaria"

        inv_x2_map = {item["product_variant_id"]: item for item in data_x2["inventory"]}
        assert var_x_id in inv_x2_map
        assert inv_x2_map[var_x_id]["stock_quantity"] == 15
        assert inv_x2_map[var_x_id]["reserved_quantity"] == 2
        assert inv_x2_map[var_x_id]["available_quantity"] == 13
        assert var_y_id not in inv_x2_map

        # 3. Requesting alien branch Y from Tenant X returns 404 (non-enumerable)
        res_alien = client.get(f"/api/v1/sync/catalog?branch_id={by1_id}", headers=headers_x)
        assert res_alien.status_code == 404
        assert res_alien.json()["detail"]["code"] == "BRANCH_NOT_FOUND"
    finally:
        _restore_db_override(prev)


def test_t1_5_1_end_to_end_legacy_migration_with_preexisting_data_and_isolation(monkeypatch):
    import importlib
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import inspect, text

    mig_t1_1_6 = importlib.import_module("backend.migrations.versions.p7l0m3n5q7r9_agregar_fundacion_saas_aditiva")
    mig_t1_1_7 = importlib.import_module("backend.migrations.versions.q8m1n4p6r8s0_backfill_tenant_legado_y_restricciones")

    engine = create_engine("sqlite:///:memory:")
    _create_pre_t1_1_6_schema(engine)

    # 1. Populate comprehensive pre-existing legacy data across multiple tables
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO roles (id, code, name, is_active) VALUES (1, 'ADMIN', 'Admin', 1)")
        conn.exec_driver_sql("INSERT INTO ciudades (id, name, is_active) VALUES (1, 'Santa Cruz', 1)")
        conn.exec_driver_sql("INSERT INTO tallas (id, name, is_active) VALUES (1, 'M', 1)")
        conn.exec_driver_sql("INSERT INTO colores (id, name, hex_code, is_active) VALUES (1, 'Azul', '#0000FF', 1)")
        conn.exec_driver_sql("INSERT INTO proveedores (id, trade_name, legal_name, tax_id, is_active) VALUES (1, 'Prov Legado', 'Prov Legado SRL', 'NIT-100', 1)")
        conn.exec_driver_sql(
            "INSERT INTO usuarios (id, role_id, first_name, last_name, email, phone, password_hash, is_active) "
            "VALUES (1, 1, 'Legacy', 'Admin', 'admin@legacy.com', '70000000', 'hash', 1)"
        )
        conn.exec_driver_sql(
            "INSERT INTO sucursales (id, city_id, name, address, phone, is_active) "
            "VALUES (1, 1, 'Sucursal Matriz', 'Av. Central 1', '70000001', 1)"
        )
        conn.exec_driver_sql("INSERT INTO usuario_sucursales (user_id, branch_id) VALUES (1, 1)")
        conn.exec_driver_sql("INSERT INTO categorias (id, name, is_active) VALUES (1, 'Vestidos', 1)")
        conn.exec_driver_sql("INSERT INTO temporadas (id, name, is_active) VALUES (1, 'Verano 2026', 1)")
        conn.exec_driver_sql("INSERT INTO colecciones (id, season_id, name, is_active) VALUES (1, 1, 'Coleccion Aurora', 1)")
        conn.exec_driver_sql(
            "INSERT INTO productos (id, category_id, season_id, collection_id, code, name, slug, price, is_active) "
            "VALUES (1, 1, 1, 1, 'PROD-001', 'Vestido Seda', 'vestido-seda', 200.00, 1)"
        )
        conn.exec_driver_sql("INSERT INTO producto_proveedores (product_id, supplier_id) VALUES (1, 1)")
        conn.exec_driver_sql("INSERT INTO variantes_producto (id, product_id, size_id, color_id, sku, is_active) VALUES (1, 1, 1, 1, 'SKU-001', 1)")
        conn.exec_driver_sql("INSERT INTO inventario (id, branch_id, product_variant_id, stock_quantity, reserved_quantity) VALUES (1, 1, 1, 50, 5)")
        conn.exec_driver_sql("INSERT INTO carritos (id, customer_id, status) VALUES (1, 1, 'ACTIVE')")
        conn.exec_driver_sql("INSERT INTO ventas (id, order_number, customer_id, branch_id, channel, status, total) VALUES (1, 'ORD-001', 1, 1, 'STORE', 'PAID', 200.00)")
        conn.exec_driver_sql("INSERT INTO pagos (id, sale_id, method, amount, status) VALUES (1, 1, 'CASH', 200.00, 'PAID')")
        conn.exec_driver_sql("INSERT INTO movimientos_inventario (id, inventory_id, movement_type, quantity, stock_before, stock_after) VALUES (1, 1, 'IN', 50, 0, 50)")

    # 2. Run additive migration (T1.1.6)
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(mig_t1_1_6, "op", op_proxy)
        mig_t1_1_6.upgrade()

    # Verify legacy tenant created
    with engine.connect() as conn:
        legacy_tenant = conn.execute(text("SELECT id, name, status FROM tenants WHERE name = 'Empresa Legado'")).fetchone()
        assert legacy_tenant is not None
        legacy_tenant_id = legacy_tenant[0]
        assert legacy_tenant[2] == "ACTIVE"

    # 3. Run backfill and constraints migration (T1.1.7)
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op_proxy = Operations(ctx)
        monkeypatch.setattr(mig_t1_1_7, "op", op_proxy)
        mig_t1_1_7.upgrade()

    # 4. Verify backfill results across all tenant-owned tables
    with engine.connect() as conn:
        for model in TENANT_OWNED_MODELS:
            tname = model.__table__.name
            null_count = conn.execute(text(f"SELECT COUNT(*) FROM {tname} WHERE tenant_id IS NULL")).scalar_one()
            assert null_count == 0, f"Table {tname} has {null_count} null tenant_id values after backfill"

            rows = conn.execute(text(f"SELECT tenant_id FROM {tname}")).fetchall()
            for r in rows:
                assert r[0] == legacy_tenant_id, f"Row in {tname} has tenant_id {r[0]} != {legacy_tenant_id}"

        # 5. Verify composite uniqueness across tenants:
        conn.execute(text("INSERT INTO tenants (id, name, status, created_at, updated_at) VALUES (2, 'Empresa Nueva', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
        conn.execute(text("INSERT INTO categorias (id, tenant_id, name, is_active) VALUES (2, 2, 'Vestidos', 1)"))
        conn.execute(text(
            "INSERT INTO productos (id, tenant_id, category_id, code, name, slug, price, is_active, created_at, updated_at) "
            "VALUES (2, 2, 2, 'PROD-001', 'Vestido Seda', 'vestido-seda-nueva', 250.00, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ))

        prods = conn.execute(text("SELECT id, tenant_id, code, price FROM productos WHERE code = 'PROD-001' ORDER BY id")).fetchall()
        assert len(prods) == 2
        assert prods[0] == (1, legacy_tenant_id, 'PROD-001', 200.0)
        assert prods[1] == (2, 2, 'PROD-001', 250.0)


def test_self_service_trial_signup_lifecycle_expiry_readonly_export_and_reactivation():
    """Verifica el flujo completo de las Fases 0, 2, 3 y 4:
    1. Alta self-service inmediata de empresa con prueba de 14 días (plan BASIC: 2 sucursales, sin IA generativa).
    2. Controles antiabuso: rechazo de empresa duplicada, correo repetido y límite por red.
    3. Verificación de correo post-ingreso y consulta enriquecida de suscripción (/subscriptions/current).
    4. Al vencer los 14 días: modo sólo lectura (permite GET y exportación 90 días, bloquea POST/PATCH/DELETE con SUBSCRIPTION_EXPIRED).
    5. Solicitud de reactivación desde la empresa y reactivación por PLATFORM_ADMIN (CU-02/CU-03), restaurando operación.
    """
    from datetime import UTC, datetime, timedelta
    from sqlalchemy import select
    from app.core.models import City, Role, Subscription as AppSub
    from app.core.seed import seed_saas_plans_and_demo_tenants

    engine, client, prev = _make_isolated_api_client()
    try:
        with Session(engine) as db:
            db.add(Role(code="ADMIN", name="Administrador", is_active=True))
            city = City(name="Santa Cruz", is_active=True)
            db.add(city)
            db.flush()
            seed_saas_plans_and_demo_tenants(db)
            db.commit()
            city_id = city.id

        # 1. Self-service trial signup -> immediate access without human approval
        signup_payload = {
            "company_name": "Atelier Solaris",
            "first_name": "Valeria",
            "last_name": "Mendoza",
            "email": "valeria@ateliersolaris.bo",
            "phone": "70011223",
            "password": "SolarisPassword1!",
        }
        res_signup = client.post("/api/v1/subscriptions/trial-signup", json=signup_payload)
        assert res_signup.status_code == 201, res_signup.text
        auth_data = res_signup.json()
        assert "access_token" in auth_data
        assert auth_data["user"]["role"] == "ADMIN"
        assert auth_data["user"]["tenant"]["name"] == "Atelier Solaris"
        tenant_id = auth_data["user"]["tenant_id"]
        headers_admin = {"Authorization": f"Bearer {auth_data['access_token']}"}

        # 2. Check duplicate company name & duplicate trial email rejection
        res_dup_name = client.post("/api/v1/subscriptions/trial-signup", json={
            **signup_payload,
            "email": "otro@ateliersolaris.bo",
        })
        assert res_dup_name.status_code == 409
        assert res_dup_name.json()["detail"]["code"] == "TENANT_NAME_EXISTS"

        res_dup_email = client.post("/api/v1/subscriptions/trial-signup", json={
            **signup_payload,
            "company_name": "Otra Boutique",
        })
        assert res_dup_email.status_code == 409
        assert res_dup_email.json()["detail"]["code"] in ("EMAIL_ALREADY_EXISTS", "TRIAL_ALREADY_USED")

        # 3. Check current subscription status: 14-day trial on BASIC (max 2 branches, no generative IA)
        res_curr = client.get("/api/v1/subscriptions/current", headers=headers_admin)
        assert res_curr.status_code == 200
        curr = res_curr.json()
        assert curr["tenant_id"] == tenant_id
        assert curr["plan"]["code"] == "BASIC"
        assert curr["max_active_branches"] == 2
        assert curr["generative_reports_enabled"] is False
        assert curr["is_trial"] is True
        assert curr["is_expired"] is False
        assert curr["read_only_mode"] is False
        assert 13 <= curr["days_remaining"] <= 14
        assert curr["email_verified"] is False

        # Verify email post-login
        res_verify = client.post("/api/v1/subscriptions/verify-email", headers=headers_admin)
        assert res_verify.status_code == 200
        assert res_verify.json()["email_verified"] is True

        # Create a branch during active trial -> allowed (up to 2)
        res_branch = client.post("/api/v1/branches", json={
            "city_id": city_id,
            "name": "Solaris Centro",
            "address": "Av. Monseñor Rivero 100",
            "phone": "3334455",
        }, headers=headers_admin)
        assert res_branch.status_code == 201

        # 4. Simulate trial expiration (14 days elapsed)
        with Session(engine) as db:
            sub = db.scalar(select(AppSub).where(AppSub.tenant_id == tenant_id))
            now = datetime.now(UTC)
            sub.valid_from = now - timedelta(days=15)
            sub.valid_until = now - timedelta(days=1)
            db.commit()

        # Check status reflects expiration, read-only mode, and 90-day retention window
        res_expired_curr = client.get("/api/v1/subscriptions/current", headers=headers_admin)
        assert res_expired_curr.status_code == 200
        exp_curr = res_expired_curr.json()
        assert exp_curr["is_expired"] is True
        assert exp_curr["read_only_mode"] is True
        assert exp_curr["days_remaining"] == 0
        assert 88 <= exp_curr["retention_days_remaining"] <= 90

        # Read operations (GET) and data export (GET /subscriptions/export) remain allowed
        res_list_branches = client.get("/api/v1/branches", headers=headers_admin)
        assert res_list_branches.status_code == 200
        assert res_list_branches.json()["total"] == 1

        res_export = client.get("/api/v1/subscriptions/export", headers=headers_admin)
        assert res_export.status_code == 200
        export_data = res_export.json()
        assert export_data["tenant"]["name"] == "Atelier Solaris"
        assert len(export_data["branches"]) == 1

        # Mutating operations (POST/PATCH/DELETE) are blocked with 403 SUBSCRIPTION_EXPIRED
        res_blocked_mutation = client.post("/api/v1/categories", json={
            "name": "Linos",
            "description": "Prendas de lino",
        }, headers=headers_admin)
        assert res_blocked_mutation.status_code == 403
        assert res_blocked_mutation.json()["detail"]["code"] == "SUBSCRIPTION_EXPIRED"

        # 5. Tenant requests reactivation from account -> allowed even when expired
        res_react_req = client.post("/api/v1/subscriptions/reactivation-request", json={
            "plan_code": "PROFESSIONAL",
            "notes": "Solicitamos activación al plan Profesional tras finalizar la prueba.",
        }, headers=headers_admin)
        assert res_react_req.status_code == 200
        assert res_react_req.json()["reactivation_requested"] is True

        # Platform Admin logs in, manages plans (CU-02) and activates subscription (CU-03)
        login_plat = client.post("/api/v1/auth/login", json={
            "email": "platform.admin@fashionstore.com",
            "password": "PlatformAdmin123!",
        })
        assert login_plat.status_code == 200
        headers_plat = {"Authorization": f"Bearer {login_plat.json()['access_token']}"}

        # CU-02: Platform admin creates and updates a plan
        res_create_plan = client.post(
            "/api/v1/platform/plans",
            json={
                "code": "ENTERPRISE",
                "name": "Empresarial",
                "price_monthly": 899.00,
                "price_annual": 8990.00,
                "currency": "BOB",
                "max_active_branches": 25,
                "generative_reports_enabled": True,
                "is_active": True,
            },
            headers=headers_plat,
        )
        assert res_create_plan.status_code == 201
        ent_plan_data = res_create_plan.json()
        assert ent_plan_data["price_monthly"] == 899.00
        assert ent_plan_data["price_annual"] == 8990.00
        assert ent_plan_data["currency"] == "BOB"
        ent_plan_id = ent_plan_data["id"]

        res_update_plan = client.patch(
            f"/api/v1/platform/plans/{ent_plan_id}",
            json={"max_active_branches": 30, "price_monthly": 999.00},
            headers=headers_plat,
        )
        assert res_update_plan.status_code == 200
        assert res_update_plan.json()["max_active_branches"] == 30
        assert res_update_plan.json()["price_monthly"] == 999.00

        # Platform admin activates PROFESSIONAL subscription for Atelier Solaris
        res_activate = client.post(
            f"/api/v1/platform/tenants/{tenant_id}/subscriptions",
            json={"plan_code": "PROFESSIONAL"},
            headers=headers_plat,
        )
        assert res_activate.status_code == 201

        # Tenant is immediately out of read-only mode and can create categories/branches again
        res_unblocked = client.post("/api/v1/categories", json={
            "name": "Linos",
            "description": "Prendas de lino",
        }, headers=headers_admin)
        assert res_unblocked.status_code == 201
    finally:
        _restore_db_override(prev)
















from decimal import Decimal

from fastapi import Depends, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.pool import StaticPool


def test_quarantine_inspection_endpoint_enforces_scope_and_idempotent_decisions():
    from app.core.database import get_db
    from app.core.models import (
        Base,
        Branch,
        Category,
        City,
        Color,
        GarmentExchange,
        GarmentExchangeItem,
        Inventory,
        InventoryMovement,
        InventoryQuarantine,
        Permission,
        Product,
        ProductVariant,
        Role,
        Sale,
        SaleItem,
        Size,
        Tenant,
        User,
    )
    from app.main import app
    from app.modules.auth.dependencies import get_current_user

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    def override_get_current_user(request: Request, db: Session = Depends(get_db)):
        actor = request.headers["x-actor"]
        return db.scalar(
            select(User)
            .options(joinedload(User.role).joinedload(Role.permissions), selectinload(User.branches))
            .where(User.email == f"{actor}@example.com")
        )

    previous_get_db = app.dependency_overrides.get(get_db)
    previous_get_current_user = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        with Session(engine) as db:
            tenant = Tenant(name="Primary Tenant")
            foreign_tenant = Tenant(name="Foreign Tenant")
            city = City(name="Test City")
            permission = Permission(code="inventory.adjust", name="Adjust inventory")
            manager_role = Role(code="BRANCH_MANAGER", name="Branch manager", permissions=[permission])
            cashier_role = Role(code="CASHIER", name="Cashier")
            admin_role = Role(code="ADMIN", name="Administrator")
            db.add_all([tenant, foreign_tenant, city, manager_role, cashier_role, admin_role])
            db.flush()

            branch = Branch(tenant=tenant, city=city, name="Primary Branch", address="Main Street", phone="70000001")
            other_branch = Branch(tenant=tenant, city=city, name="Other Branch", address="Other Street", phone="70000002")
            db.add_all([branch, other_branch])
            db.flush()

            manager = User(
                tenant=tenant,
                role=manager_role,
                first_name="Branch",
                last_name="Manager",
                email="manager@example.com",
                phone="70000003",
                password_hash="unused",
                branches=[branch],
            )
            other_branch_manager = User(
                tenant=tenant,
                role=manager_role,
                first_name="Other",
                last_name="Manager",
                email="other-branch@example.com",
                phone="70000004",
                password_hash="unused",
                branches=[other_branch],
            )
            cashier = User(
                tenant=tenant,
                role=cashier_role,
                first_name="Store",
                last_name="Cashier",
                email="cashier@example.com",
                phone="70000005",
                password_hash="unused",
                branches=[branch],
            )
            foreign_admin = User(
                tenant=foreign_tenant,
                role=admin_role,
                first_name="Foreign",
                last_name="Admin",
                email="foreign-admin@example.com",
                phone="70000006",
                password_hash="unused",
            )
            db.add_all([manager, other_branch_manager, cashier, foreign_admin])

            category = Category(tenant=tenant, name="Test Category")
            size = Size(name="Test M")
            color = Color(name="Test Blue", hex_code="#0000FF")
            product = Product(
                tenant=tenant,
                category=category,
                code="TEST-001",
                name="Test Shirt",
                slug="test-shirt",
                price=Decimal("100.00"),
            )
            variant = ProductVariant(tenant=tenant, product=product, size=size, color=color, sku="TEST-001-M-BLUE")
            db.add_all([category, size, color, product, variant])
            db.flush()

            inventory = Inventory(
                tenant=tenant,
                branch=branch,
                product_variant=variant,
                stock_quantity=5,
                reserved_quantity=0,
            )
            sale = Sale(
                tenant=tenant,
                branch_id=branch.id,
                order_number="TEST-ORDER-001",
                channel="PHYSICAL",
                status="CONFIRMED",
                subtotal=Decimal("200.00"),
                discount=Decimal("0.00"),
                total=Decimal("200.00"),
            )
            db.add_all([inventory, sale])
            db.flush()

            first_sale_item = SaleItem(
                sale=sale,
                product_variant=variant,
                quantity=2,
                unit_price=Decimal("100.00"),
                discount=Decimal("0.00"),
                line_total=Decimal("200.00"),
            )
            second_sale_item = SaleItem(
                sale=sale,
                product_variant=variant,
                quantity=3,
                unit_price=Decimal("100.00"),
                discount=Decimal("0.00"),
                line_total=Decimal("300.00"),
            )
            db.add_all([first_sale_item, second_sale_item])
            db.flush()

            first_exchange = GarmentExchange(
                tenant=tenant,
                sale=sale,
                branch_id=branch.id,
                idempotency_key="exchange-001",
                request_fingerprint="fingerprint-001",
                returned_value=Decimal("200.00"),
                delivered_value=Decimal("200.00"),
                difference=Decimal("0.00"),
                cashier_confirmed=True,
                result_json={},
            )
            second_exchange = GarmentExchange(
                tenant=tenant,
                sale=sale,
                branch_id=branch.id,
                idempotency_key="exchange-002",
                request_fingerprint="fingerprint-002",
                returned_value=Decimal("300.00"),
                delivered_value=Decimal("300.00"),
                difference=Decimal("0.00"),
                cashier_confirmed=True,
                result_json={},
            )
            db.add_all([first_exchange, second_exchange])
            db.flush()

            first_exchange_item = GarmentExchangeItem(
                exchange=first_exchange,
                sale_item=first_sale_item,
                returned_quantity=2,
                new_variant_id=variant.id,
                new_quantity=2,
            )
            second_exchange_item = GarmentExchangeItem(
                exchange=second_exchange,
                sale_item=second_sale_item,
                returned_quantity=3,
                new_variant_id=variant.id,
                new_quantity=3,
            )
            db.add_all([first_exchange_item, second_exchange_item])
            db.flush()

            first_quarantine = InventoryQuarantine(
                tenant=tenant,
                branch=branch,
                inventory=inventory,
                product_variant=variant,
                exchange_item=first_exchange_item,
                quantity=2,
            )
            second_quarantine = InventoryQuarantine(
                tenant=tenant,
                branch=branch,
                inventory=inventory,
                product_variant=variant,
                exchange_item=second_exchange_item,
                quantity=3,
            )
            db.add_all([first_quarantine, second_quarantine])
            db.commit()
            first_quarantine_id = first_quarantine.id
            second_quarantine_id = second_quarantine.id
            inventory_id = inventory.id

        client = TestClient(app)
        release_payload = {"decision": "RELEASE", "reason": "Passed inspection"}
        reject_payload = {"decision": "REJECT", "reason": "Damaged"}

        assert client.post(
            f"/api/v1/inventory/quarantine/{first_quarantine_id}/inspection",
            json=release_payload,
            headers={"x-actor": "cashier"},
        ).status_code == 403
        assert client.post(
            f"/api/v1/inventory/quarantine/{first_quarantine_id}/inspection",
            json=release_payload,
            headers={"x-actor": "other-branch"},
        ).status_code == 403
        foreign_response = client.post(
            f"/api/v1/inventory/quarantine/{first_quarantine_id}/inspection",
            json=release_payload,
            headers={"x-actor": "foreign-admin"},
        )
        assert foreign_response.status_code == 404
        assert foreign_response.json()["detail"]["code"] == "QUARANTINE_NOT_FOUND"

        released = client.post(
            f"/api/v1/inventory/quarantine/{first_quarantine_id}/inspection",
            json=release_payload,
            headers={"x-actor": "manager"},
        )
        assert released.status_code == 200, released.text
        assert released.json()["status"] == "RELEASED"

        with Session(engine) as db:
            assert db.get(Inventory, inventory_id).stock_quantity == 7
            assert db.scalar(select(func.count(InventoryMovement.id)).where(InventoryMovement.movement_type == "IN")) == 1

        repeated = client.post(
            f"/api/v1/inventory/quarantine/{first_quarantine_id}/inspection",
            json=release_payload,
            headers={"x-actor": "manager"},
        )
        assert repeated.status_code == 200
        with Session(engine) as db:
            assert db.scalar(select(func.count(InventoryMovement.id)).where(InventoryMovement.movement_type == "IN")) == 1

        opposite = client.post(
            f"/api/v1/inventory/quarantine/{first_quarantine_id}/inspection",
            json=reject_payload,
            headers={"x-actor": "manager"},
        )
        assert opposite.status_code == 409

        rejected = client.post(
            f"/api/v1/inventory/quarantine/{second_quarantine_id}/inspection",
            json=reject_payload,
            headers={"x-actor": "manager"},
        )
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["status"] == "REJECTED"
        with Session(engine) as db:
            assert db.get(Inventory, inventory_id).stock_quantity == 7
            assert db.scalar(select(func.count(InventoryMovement.id)).where(InventoryMovement.movement_type == "IN")) == 1
    finally:
        if previous_get_db is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_get_db
        if previous_get_current_user is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous_get_current_user

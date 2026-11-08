from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.models import (
    Base,
    Branch,
    City,
    Role,
    SyncOperation,
    Tenant,
    User,
)


def test_cu13_exchange_request_requires_idempotency_and_cash_confirmation():
    from app.modules.commerce.schemas import ItemExchangeRequest

    request = ItemExchangeRequest(
        returned_variant_id=1,
        returned_quantity=1,
        new_variant_id=2,
        new_quantity=1,
        idempotency_key="exchange-001",
        quote_fingerprint="a" * 64,
        quote_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        cashier_confirmed=True,
    )

    assert request.idempotency_key == "exchange-001"
    assert request.cashier_confirmed is True


def test_cu13_exchange_idempotency_collision_rolls_back_and_replays_winner():
    from types import SimpleNamespace

    from app.modules.commerce import service

    winner = SimpleNamespace(request_fingerprint="same-hash", result_json={"status": "EXCHANGED"})
    rollback_state = {"called": False}

    class CollisionDatabase:
        def flush(self):
            raise IntegrityError(
                "INSERT",
                {},
                Exception("uq_garment_exchanges_tenant_idempotency"),
            )

        def rollback(self):
            rollback_state["called"] = True

        def scalar(self, statement):
            assert rollback_state["called"] is True
            return winner

    exchange = SimpleNamespace(tenant_id=7, idempotency_key="exchange-001")
    replay = service._flush_exchange_or_replay(CollisionDatabase(), exchange, "same-hash")

    assert replay == {"status": "EXCHANGED"}
    assert rollback_state["called"] is True


def test_cu13_nonzero_difference_requires_all_settled_tenders_to_be_cash():
    from types import SimpleNamespace

    from app.modules.commerce import service

    assert service._is_cash_origin([SimpleNamespace(method="CASH", status="APPROVED")]) is True
    assert service._is_cash_origin([
        SimpleNamespace(method="CASH", status="APPROVED"),
        SimpleNamespace(method="CARD", status="APPROVED"),
    ]) is False
    assert service._is_cash_origin([SimpleNamespace(method="CARD", status="APPROVED")]) is False
    assert service._is_cash_origin([
        SimpleNamespace(method="CASH", status="APPROVED"),
        SimpleNamespace(method="CARD", status="PENDING"),
    ]) is False


def test_cu13_cash_refund_is_outgoing_exchange_adjustment_not_payment_change():
    from decimal import Decimal

    from app.modules.commerce import service

    settlement = service._exchange_cash_settlement(Decimal("-20.00"), None)

    assert settlement["cash_refunded"] == Decimal("20.00")
    assert settlement["cash_change"] is None
    assert settlement["create_payment"] is False


def test_t2_1_1_sync_operation_model_round_trip_and_constraints():
    """T2.1.1: Verify SyncOperation ORM model round-trip, relationships, and uniqueness constraints."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Create tenant, city, branch, role, user
        tenant = Tenant(name="Tenant A", status="ACTIVE")
        city = City(name="La Paz", is_active=True)
        session.add_all([tenant, city])
        session.flush()

        branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Sucursal Central", address="Av. 16 de Julio", phone="2222222")
        role = Role(code="CASHIER", name="Cajero")
        session.add_all([branch, role])
        session.flush()

        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            first_name="Juan",
            last_name="Perez",
            email="cajero@tenanta.com",
            phone="70000001",
            password_hash="hashed",
            is_active=True,
        )
        session.add(user)
        session.flush()

        # Create SyncOperation for SALE
        sync_op = SyncOperation(
            tenant_id=tenant.id,
            client_operation_id="uuid-op-001",
            branch_id=branch.id,
            user_id=user.id,
            operation_type="SALE",
            status="CONFIRMED",
            payload={"items": [{"variant_id": 1, "quantity": 2, "unit_price": 50.0}], "total": 100.0},
            conflict_detail=None,
        )
        session.add(sync_op)
        session.commit()

        # Query back
        stored = session.query(SyncOperation).filter_by(client_operation_id="uuid-op-001").one()
        assert stored.tenant_id == tenant.id
        assert stored.operation_type == "SALE"
        assert stored.status == "CONFIRMED"
        assert stored.payload["total"] == 100.0
        assert stored.tenant.name == "Tenant A"
        assert stored.branch.name == "Sucursal Central"
        assert stored.user.email == "cajero@tenanta.com"
        assert stored.created_at is not None

        # Verify idempotency constraint: (tenant_id, client_operation_id) must be unique
        duplicate_op = SyncOperation(
            tenant_id=tenant.id,
            client_operation_id="uuid-op-001",
            branch_id=branch.id,
            user_id=user.id,
            operation_type="SALE",
            status="CONFIRMED",
            payload={"items": []},
        )
        session.add(duplicate_op)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_t2_1_2_migration_sync_operations_revision_graph_and_ddl(monkeypatch):
    """T2.1.2: Verify Alembic migration r9n2p5q7s9t1 revises q8m1n4p6r8s0 and generates valid PostgreSQL DDL."""
    import importlib
    from io import StringIO
    from pathlib import Path
    from alembic.config import Config
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy.dialects import postgresql

    alembic_cfg = Config()
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    rev = script_dir.get_revision("r9n2p5q7s9t1")
    assert rev is not None, "Expected revision r9n2p5q7s9t1 to exist"
    assert rev.down_revision == "q8m1n4p6r8s0", "Expected r9n2p5q7s9t1 to revise q8m1n4p6r8s0"
    assert "r9n2p5q7s9t1" in {r.revision for r in script_dir.walk_revisions()}

    try:
        migration_mod = importlib.import_module(
            "backend.migrations.versions.r9n2p5q7s9t1_crear_tabla_sync_operations"
        )
    except ModuleNotFoundError:
        migration_mod = importlib.import_module(
            "migrations.versions.r9n2p5q7s9t1_crear_tabla_sync_operations"
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
    assert "CREATE TABLE sync_operations" in sql
    assert "client_operation_id" in sql
    assert "uq_sync_operations_tenant_client_op_id" in sql
    assert "ck_sync_operations_type" in sql
    assert "ck_sync_operations_status" in sql

    # Test downgrade
    buf_down = StringIO()
    ctx_down = MigrationContext.configure(
        dialect=postgresql.dialect(),
        opts={"as_sql": True, "output_buffer": buf_down},
    )
    op_proxy_down = Operations(ctx_down)
    monkeypatch.setattr(migration_mod, "op", op_proxy_down)
    migration_mod.downgrade()

    sql_down = buf_down.getvalue()
    assert "DROP TABLE sync_operations" in sql_down


def test_t2_1_3_sync_transaction_schemas_validation():
    """T2.1.3: Verify Pydantic schemas for offline sync requests and batch responses."""
    from decimal import Decimal
    from app.modules.sync.schemas import (
        OfflineSaleItemPayload,
        OfflineSalePayload,
        OfflineReservationItemPayload,
        OfflineReservationPayload,
        SyncTransactionItemRequest,
        SyncTransactionBatchRequest,
        SyncConflictDetail,
        SyncTransactionItemResult,
        SyncTransactionBatchResponse,
    )

    sale_item = OfflineSaleItemPayload(product_variant_id=10, quantity=2, unit_price=Decimal("45.50"))
    assert sale_item.quantity == 2

    sale_payload = OfflineSalePayload(
        customer_id=None,
        items=[sale_item],
        discount=Decimal("0.00"),
        total=Decimal("91.00"),
        payment_method="CASH",
    )
    assert sale_payload.total == Decimal("91.00")

    op_req = SyncTransactionItemRequest(
        client_operation_id="uuid-batch-1",
        branch_id=1,
        operation_type="SALE",
        sale_payload=sale_payload,
    )
    assert op_req.operation_type == "SALE"

    batch_req = SyncTransactionBatchRequest(operations=[op_req])
    assert len(batch_req.operations) == 1

    # Conflict detail schema
    conflict = SyncConflictDetail(
        code="INSUFFICIENT_STOCK",
        message="Stock insuficiente para la variante 10",
        variant_id=10,
        sku="SKU-10-M",
        requested_quantity=2,
        available_quantity=0,
    )
    assert conflict.available_quantity == 0

    item_result = SyncTransactionItemResult(
        client_operation_id="uuid-batch-1",
        operation_type="SALE",
        status="CONFLICT",
        conflict_detail=conflict,
        processed_at=datetime.now(timezone.utc),
    )
    assert item_result.status == "CONFLICT"

    batch_res = SyncTransactionBatchResponse(
        processed_count=1,
        confirmed_count=0,
        conflict_count=1,
        results=[item_result],
    )
    assert batch_res.conflict_count == 1


def test_t2_1_4_sync_service_sales_reservations_idempotency_and_conflicts():
    """T2.1.4: Verify service logic for offline sales, reservations, stock consistency, conflicts, and idempotency."""
    from decimal import Decimal
    from app.core.models import (
        Category,
        Color,
        Inventory,
        InventoryMovement,
        Payment,
        Product,
        ProductVariant,
        Reservation,
        Sale,
        Size,
    )
    from app.modules.sync.schemas import (
        OfflineSaleItemPayload,
        OfflineSalePayload,
        OfflineReservationItemPayload,
        OfflineReservationPayload,
        SyncTransactionBatchRequest,
        SyncTransactionItemRequest,
    )
    from app.modules.sync.service import process_sync_transactions_batch

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Setup Tenant, Branch, User
        tenant = Tenant(name="Empresa Moda", status="ACTIVE")
        other_tenant = Tenant(name="Empresa Ajena", status="ACTIVE")
        city = City(name="Cochabamba", is_active=True)
        session.add_all([tenant, other_tenant, city])
        session.flush()

        branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Sucursal 1", address="Calle Calama", phone="4444444")
        alien_branch = Branch(tenant_id=other_tenant.id, city_id=city.id, name="Sucursal Ajena", address="Av. Heroinas", phone="4444445")
        role = Role(code="CASHIER", name="Cajero")
        session.add_all([branch, alien_branch, role])
        session.flush()

        cashier = User(
            tenant_id=tenant.id,
            role_id=role.id,
            first_name="Carlos",
            last_name="Gomez",
            email="carlos@moda.local",
            phone="71111111",
            password_hash="secret",
            is_active=True,
        )
        session.add(cashier)
        session.flush()

        # Setup Product, Variant, Inventory
        category = Category(tenant_id=tenant.id, name="Camisas", is_active=True)
        size = Size(name="M", sort_order=1)
        color = Color(name="Azul", hex_code="#0000FF")
        session.add_all([category, size, color])
        session.flush()

        product = Product(
            tenant_id=tenant.id,
            category_id=category.id,
            name="Camisa Formal",
            code="CAM-001",
            slug="camisa-formal",
            price=Decimal("120.00"),
            is_active=True,
        )
        session.add(product)
        session.flush()

        variant = ProductVariant(
            tenant_id=tenant.id,
            product_id=product.id,
            size_id=size.id,
            color_id=color.id,
            sku="CAM-001-M-AZUL",
            is_active=True,
        )
        session.add(variant)
        session.flush()

        inv = Inventory(
            tenant_id=tenant.id,
            branch_id=branch.id,
            product_variant_id=variant.id,
            stock_quantity=5,
            reserved_quantity=0,
        )
        session.add(inv)
        session.commit()

        # Case 1: Sale with sufficient stock (3 units out of 5)
        sale_req = SyncTransactionItemRequest(
            client_operation_id="op-sale-101",
            branch_id=branch.id,
            operation_type="SALE",
            sale_payload=OfflineSalePayload(
                items=[OfflineSaleItemPayload(product_variant_id=variant.id, quantity=3, unit_price=Decimal("120.00"))],
                total=Decimal("360.00"),
            ),
        )

        res = process_sync_transactions_batch(session, cashier, SyncTransactionBatchRequest(operations=[sale_req]))
        assert res.processed_count == 1
        assert res.confirmed_count == 1
        assert res.conflict_count == 0
        assert res.results[0].status == "CONFIRMED"
        assert res.results[0].sale_id is not None

        # Verify DB effects
        session.refresh(inv)
        assert inv.stock_quantity == 2, "Stock must decrement from 5 to 2"

        sale = session.query(Sale).filter_by(id=res.results[0].sale_id).one()
        assert sale.total == Decimal("360.00")
        assert sale.channel == "PHYSICAL"
        assert sale.status == "COMPLETED"

        payment = session.query(Payment).filter_by(sale_id=sale.id).one()
        assert payment.method == "CASH"
        assert payment.status == "APPROVED"
        assert payment.amount == Decimal("360.00")

        movement = session.query(InventoryMovement).filter_by(reference_id=sale.id).one()
        assert movement.movement_type == "SALE"
        assert movement.quantity == 3
        assert movement.stock_before == 5
        assert movement.stock_after == 2

        # Case 2: Idempotency check - resubmit identical operation
        res_dup = process_sync_transactions_batch(session, cashier, SyncTransactionBatchRequest(operations=[sale_req]))
        assert res_dup.processed_count == 1
        assert res_dup.confirmed_count == 1
        assert res_dup.results[0].status == "CONFIRMED"
        assert res_dup.results[0].sale_id == sale.id

        session.refresh(inv)
        assert inv.stock_quantity == 2, "Stock must NOT decrement again on duplicate operation"

        # Case 3: Sale with insufficient stock (wants 4 units, but only 2 remain)
        insufficient_sale_req = SyncTransactionItemRequest(
            client_operation_id="op-sale-102",
            branch_id=branch.id,
            operation_type="SALE",
            sale_payload=OfflineSalePayload(
                items=[OfflineSaleItemPayload(product_variant_id=variant.id, quantity=4, unit_price=Decimal("120.00"))],
                total=Decimal("480.00"),
            ),
        )

        res_conflict = process_sync_transactions_batch(session, cashier, SyncTransactionBatchRequest(operations=[insufficient_sale_req]))
        assert res_conflict.processed_count == 1
        assert res_conflict.confirmed_count == 0
        assert res_conflict.conflict_count == 1
        assert res_conflict.results[0].status == "CONFLICT"
        assert res_conflict.results[0].conflict_detail is not None
        assert res_conflict.results[0].conflict_detail.code == "INSUFFICIENT_STOCK"
        assert res_conflict.results[0].conflict_detail.requested_quantity == 4
        assert res_conflict.results[0].conflict_detail.available_quantity == 2

        session.refresh(inv)
        assert inv.stock_quantity == 2, "Stock must remain unchanged after conflict"

        # Case 4: Reservation with available stock (wants 1 unit out of 2)
        resv_req = SyncTransactionItemRequest(
            client_operation_id="op-resv-201",
            branch_id=branch.id,
            operation_type="RESERVATION",
            reservation_payload=OfflineReservationPayload(
                customer_name="Maria Lopez",
                customer_phone="72222222",
                items=[OfflineReservationItemPayload(product_variant_id=variant.id, quantity=1)],
            ),
        )

        res_resv = process_sync_transactions_batch(session, cashier, SyncTransactionBatchRequest(operations=[resv_req]))
        assert res_resv.confirmed_count == 1
        assert res_resv.results[0].status == "CONFIRMED"
        assert res_resv.results[0].reservation_id is not None

        session.refresh(inv)
        assert inv.reserved_quantity == 1, "Reserved quantity must increment by 1"

        # Case 5: Alien branch rejection (security / multi-tenant boundary)
        alien_req = SyncTransactionItemRequest(
            client_operation_id="op-alien-999",
            branch_id=alien_branch.id,
            operation_type="SALE",
            sale_payload=OfflineSalePayload(
                items=[OfflineSaleItemPayload(product_variant_id=variant.id, quantity=1, unit_price=Decimal("120.00"))],
                total=Decimal("120.00"),
            ),
        )

        res_alien = process_sync_transactions_batch(session, cashier, SyncTransactionBatchRequest(operations=[alien_req]))
        assert res_alien.conflict_count == 1 or res_alien.results[0].status in ("REJECTED", "CONFLICT")
        assert res_alien.results[0].conflict_detail.code == "BRANCH_NOT_FOUND"


def test_t2_1_5_t2_1_6_api_endpoints_sync_transactions_and_exchange():
    """T2.1.5 & T2.1.6: Verify REST endpoints for POST /sync/transactions, GET status, and POST /commerce/sales/{id}/exchange."""
    from decimal import Decimal
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select
    from sqlalchemy.pool import StaticPool
    from app.core.database import get_db
    from app.core.models import (
        Category,
        Color,
        GarmentExchange,
        Inventory,
        InventoryQuarantine,
        Payment,
        Permission,
        Product,
        Sale,
        ProductVariant,
        Role,
        RolePermission,
        Size,
    )
    from app.core.security import hash_password
    from app.main import app

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def _override_db():
        with Session(engine) as session:
            yield session

    prev = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    try:
        with Session(engine) as db:
            tenant = Tenant(name="Tienda Viva", status="ACTIVE")
            city = City(name="La Paz", is_active=True)
            db.add_all([tenant, city])
            db.flush()

            branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Sucursal Miraflores", address="Av. Busch", phone="2222222")
            other_branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Sucursal Norte", address="Av. Arce", phone="2222223")
            role_cashier = Role(code="CASHIER", name="Cajero")
            role_admin = Role(code="ADMIN", name="Administrador")
            role_manager = Role(code="BRANCH_MANAGER", name="Encargado de sucursal")
            sales_read = Permission(code="sales.read", name="Consultar ventas")
            db.add_all([branch, other_branch, role_cashier, role_admin, role_manager, sales_read])
            db.flush()
            db.add(RolePermission(role_id=role_manager.id, permission_id=sales_read.id))

            cashier = User(
                tenant_id=tenant.id,
                role_id=role_admin.id,  # Admin has all permissions including commerce
                first_name="Marco",
                last_name="Paz",
                email="admin@tiendaviva.com",
                phone="70000010",
                password_hash=hash_password("Pass123!"),
                is_active=True,
            )
            cashier.branches.append(branch)
            manager = User(
                tenant_id=tenant.id,
                role_id=role_manager.id,
                first_name="Nora",
                last_name="Norte",
                email="manager@tiendaviva.com",
                phone="70000011",
                password_hash=hash_password("Manager123!"),
                is_active=True,
            )
            manager.branches.append(other_branch)
            db.add_all([cashier, manager])

            cat = Category(tenant_id=tenant.id, name="Pantalones", is_active=True)
            sz1 = Size(name="30", sort_order=1)
            sz2 = Size(name="32", sort_order=2)
            col = Color(name="Negro", hex_code="#000000")
            db.add_all([cat, sz1, sz2, col])
            db.flush()

            prod = Product(tenant_id=tenant.id, category_id=cat.id, name="Jeans Slim", code="JNS-001", slug="jeans-slim", price=Decimal("150.00"), is_active=True)
            prod_expensive = Product(tenant_id=tenant.id, category_id=cat.id, name="Jeans Premium", code="JNS-002", slug="jeans-premium", price=Decimal("180.00"), is_active=True)
            prod_cheap = Product(tenant_id=tenant.id, category_id=cat.id, name="Jeans Basic", code="JNS-003", slug="jeans-basic", price=Decimal("100.00"), is_active=True)
            db.add_all([prod, prod_expensive, prod_cheap])
            db.flush()

            v1 = ProductVariant(tenant_id=tenant.id, product_id=prod.id, size_id=sz1.id, color_id=col.id, sku="JNS-30-NEG", is_active=True)
            v2 = ProductVariant(tenant_id=tenant.id, product_id=prod.id, size_id=sz2.id, color_id=col.id, sku="JNS-32-NEG", is_active=True)
            v3 = ProductVariant(tenant_id=tenant.id, product_id=prod_expensive.id, size_id=sz1.id, color_id=col.id, sku="JNS-PREMIUM-NEG", is_active=True)
            v4 = ProductVariant(tenant_id=tenant.id, product_id=prod_cheap.id, size_id=sz1.id, color_id=col.id, sku="JNS-BASIC-NEG", is_active=True)
            db.add_all([v1, v2, v3, v4])
            db.flush()

            inv1 = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=v1.id, stock_quantity=10, reserved_quantity=0)
            inv2 = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=v2.id, stock_quantity=5, reserved_quantity=0)
            inv3 = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=v3.id, stock_quantity=5, reserved_quantity=0)
            inv4 = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=v4.id, stock_quantity=5, reserved_quantity=0)
            db.add_all([inv1, inv2, inv3, inv4])
            db.commit()

            v1_id, v2_id, v3_id, v4_id, v2_product_id, b_id, tenant_id = v1.id, v2.id, v3.id, v4.id, prod.id, branch.id, tenant.id

        # 1. Login
        login_res = client.post("/api/v1/auth/login", json={"email": "admin@tiendaviva.com", "password": "Pass123!"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. POST /api/v1/sync/transactions
        batch_payload = {
            "operations": [
                {
                    "client_operation_id": "op-api-101",
                    "branch_id": b_id,
                    "operation_type": "SALE",
                    "sale_payload": {
                        "items": [{"product_variant_id": v1_id, "quantity": 3, "unit_price": 150.0}],
                        "total": 450.0,
                    },
                },
                {
                    "client_operation_id": "op-api-102",
                    "branch_id": b_id,
                    "operation_type": "SALE",
                    "sale_payload": {
                        "items": [{"product_variant_id": v1_id, "quantity": 999, "unit_price": 150.0}],
                        "total": 149850.0,
                    },
                },
            ]
        }
        res_sync = client.post("/api/v1/sync/transactions", json=batch_payload, headers=headers)
        assert res_sync.status_code == 200, res_sync.text
        data_sync = res_sync.json()
        assert data_sync["processed_count"] == 2
        assert data_sync["confirmed_count"] == 1
        assert data_sync["conflict_count"] == 1

        op1 = next(r for r in data_sync["results"] if r["client_operation_id"] == "op-api-101")
        assert op1["status"] == "CONFIRMED"
        assert op1["sale_id"] is not None
        confirmed_sale_id = op1["sale_id"]

        op2 = next(r for r in data_sync["results"] if r["client_operation_id"] == "op-api-102")
        assert op2["status"] == "CONFLICT"
        assert op2["conflict_detail"]["code"] == "INSUFFICIENT_STOCK"

        # 3. GET /api/v1/sync/transactions/{client_operation_id}
        res_status = client.get("/api/v1/sync/transactions/op-api-101", headers=headers)
        assert res_status.status_code == 200
        status_data = res_status.json()
        assert status_data["client_operation_id"] == "op-api-101"
        assert status_data["status"] == "CONFIRMED"
        assert status_data["sale_id"] == confirmed_sale_id

        # 4. Lookup and quote expose server-derived exchange data.
        with Session(engine) as db:
            sale_order_number = db.scalar(select(Sale.order_number).where(Sale.id == confirmed_sale_id))
        lookup_res = client.get(f"/api/v1/sales/lookup/{sale_order_number}", headers=headers)
        assert lookup_res.status_code == 200, lookup_res.text
        lookup_item = lookup_res.json()["items"][0]
        assert lookup_item["purchased_quantity"] == 3
        assert lookup_item["remaining_exchangeable_quantity"] == 3
        assert lookup_item["net_paid_line_total"] == "450.00"

        manager_login = client.post("/api/v1/auth/login", json={"email": "manager@tiendaviva.com", "password": "Manager123!"})
        assert manager_login.status_code == 200
        manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}
        manager_lookup = client.get(f"/api/v1/sales/lookup/{sale_order_number}", headers=manager_headers)
        assert manager_lookup.status_code == 404
        assert manager_lookup.json()["detail"]["code"] == "SALE_NOT_FOUND"

        exchange_payload = {
            "returned_variant_id": v1_id,
            "returned_quantity": 1,
            "new_variant_id": v2_id,
            "new_quantity": 1,
            "idempotency_key": "exchange-api-101",
            "reason": "Cambio por talla 32",
        }
        quote_request = {k: exchange_payload[k] for k in ("returned_variant_id", "returned_quantity", "new_variant_id", "new_quantity")}
        quote_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange/quote", json=quote_request, headers=headers)
        assert quote_res.status_code == 200, quote_res.text
        quote_data = quote_res.json()
        assert quote_data["returned_value"] == "150.00"
        assert quote_data["replacement_unit_price"] == "150.00"
        assert quote_data["available_stock"] == 5
        assert quote_data["cash_settlement_eligible"] is True

        with Session(engine) as db:
            before_inv = db.scalar(select(Inventory).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            before_exchange_count = db.scalar(select(func.count(GarmentExchange.id)))
            before_quarantine_count = db.scalar(select(func.count(InventoryQuarantine.id)))
            before_payment_count = db.scalar(select(func.count(Payment.id)))
            before_stock = before_inv.stock_quantity
        stale_payload = {**exchange_payload, "idempotency_key": "exchange-api-stale", "quote_fingerprint": quote_data["quote_fingerprint"], "quote_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}
        stale_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=stale_payload, headers=headers)
        assert stale_res.status_code == 409, stale_res.text
        assert stale_res.json()["detail"]["code"] == "EXCHANGE_QUOTE_STALE"
        with Session(engine) as db:
            after_inv = db.scalar(select(Inventory).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            assert after_inv.stock_quantity == before_stock
            assert db.scalar(select(func.count(GarmentExchange.id))) == before_exchange_count
            assert db.scalar(select(func.count(InventoryQuarantine.id))) == before_quarantine_count
            assert db.scalar(select(func.count(Payment.id))) == before_payment_count

        exchange_payload.update({"quote_fingerprint": quote_data["quote_fingerprint"], "quote_expires_at": quote_data["expires_at"]})
        res_exchange = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=exchange_payload, headers=headers)
        assert res_exchange.status_code == 200, res_exchange.text
        ex_data = res_exchange.json()
        assert ex_data["status"] == "EXCHANGED"
        assert ex_data["sale_id"] == confirmed_sale_id
        assert ex_data["quarantine_id"] is not None
        assert ex_data["quarantine_status"] == "PENDING"
        lookup_after_exchange = client.get(f"/api/v1/sales/lookup/{sale_order_number}", headers=headers)
        assert lookup_after_exchange.status_code == 200, lookup_after_exchange.text
        assert lookup_after_exchange.json()["items"][0]["remaining_exchangeable_quantity"] == 2
        queue_res = client.get("/api/v1/inventory/quarantine?status=PENDING", headers=headers)
        assert queue_res.status_code == 200, queue_res.text
        assert any(item["id"] == ex_data["quarantine_id"] and item["status"] == "PENDING" for item in queue_res.json()["items"])

        # Verify DB stock after exchange: v1 was 10, sold 3 (became 7), returned 1 remains quarantined
        # v2 was 5, exchanged 1 (must be 4)
        with Session(engine) as db:
            inv1_db = db.scalar(select(Inventory).where(Inventory.product_variant_id == v1_id, Inventory.branch_id == b_id))
            inv2_db = db.scalar(select(Inventory).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            assert inv1_db.stock_quantity == 7, "Returned variant must not be sellable before inspection"
            assert inv2_db.stock_quantity == 4, "New variant stock must be 4"
            quarantine_db = db.scalar(select(InventoryQuarantine).where(InventoryQuarantine.id == ex_data["quarantine_id"]))
            assert quarantine_db is not None
            assert quarantine_db.status == "PENDING"
            exchange_db = db.scalar(select(GarmentExchange).where(GarmentExchange.idempotency_key == "exchange-api-101"))
            assert exchange_db.result_json["quarantine_id"] == ex_data["quarantine_id"]
            assert exchange_db.result_json["quarantine_status"] == "PENDING"

        # A fresh quote must become stale when replacement stock changes, even if enough stock remains.
        stock_quote_request = {"returned_variant_id": v1_id, "returned_quantity": 1, "new_variant_id": v2_id, "new_quantity": 1}
        stock_quote_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange/quote", json=stock_quote_request, headers=headers)
        assert stock_quote_res.status_code == 200, stock_quote_res.text
        stock_quote = stock_quote_res.json()
        with Session(engine) as db:
            inv2_db = db.scalar(select(Inventory).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            before_stock_stale = inv2_db.stock_quantity
            before_exchange_count = db.scalar(select(func.count(GarmentExchange.id)))
            before_quarantine_count = db.scalar(select(func.count(InventoryQuarantine.id)))
            before_payment_count = db.scalar(select(func.count(Payment.id)))
            inv2_db.stock_quantity = before_stock_stale - 1
            db.commit()
        stock_stale_payload = {**stock_quote_request, "idempotency_key": "exchange-api-stock-stale", "quote_fingerprint": stock_quote["quote_fingerprint"], "quote_expires_at": stock_quote["expires_at"]}
        stock_stale_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=stock_stale_payload, headers=headers)
        assert stock_stale_res.status_code == 409, stock_stale_res.text
        assert stock_stale_res.json()["detail"]["code"] == "EXCHANGE_QUOTE_STALE"
        with Session(engine) as db:
            inv2_db = db.scalar(select(Inventory).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            assert inv2_db.stock_quantity == before_stock_stale - 1
            assert db.scalar(select(func.count(GarmentExchange.id))) == before_exchange_count
            assert db.scalar(select(func.count(InventoryQuarantine.id))) == before_quarantine_count
            assert db.scalar(select(func.count(Payment.id))) == before_payment_count
            inv2_db.stock_quantity = before_stock_stale
            db.commit()

        # A fresh quote must also become stale when the replacement price changes.
        price_quote_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange/quote", json=stock_quote_request, headers=headers)
        assert price_quote_res.status_code == 200, price_quote_res.text
        price_quote = price_quote_res.json()
        with Session(engine) as db:
            before_exchange_count = db.scalar(select(func.count(GarmentExchange.id)))
            before_quarantine_count = db.scalar(select(func.count(InventoryQuarantine.id)))
            before_payment_count = db.scalar(select(func.count(Payment.id)))
            prod_db = db.scalar(select(Product).where(Product.id == v2_product_id))
            original_price = prod_db.price
            prod_db.price = original_price + Decimal("10.00")
            db.commit()
        price_stale_payload = {**stock_quote_request, "idempotency_key": "exchange-api-price-stale", "quote_fingerprint": price_quote["quote_fingerprint"], "quote_expires_at": price_quote["expires_at"], "cash_tendered": 10}
        price_stale_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=price_stale_payload, headers=headers)
        assert price_stale_res.status_code == 409, price_stale_res.text
        assert price_stale_res.json()["detail"]["code"] == "EXCHANGE_QUOTE_STALE"
        with Session(engine) as db:
            assert db.scalar(select(func.count(GarmentExchange.id))) == before_exchange_count
            assert db.scalar(select(func.count(InventoryQuarantine.id))) == before_quarantine_count
            assert db.scalar(select(func.count(Payment.id))) == before_payment_count
            prod_db = db.scalar(select(Product).where(Product.id == v2_product_id))
            prod_db.price = original_price
            db.commit()

        expired_quote_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange/quote", json=stock_quote_request, headers=headers)
        assert expired_quote_res.status_code == 200, expired_quote_res.text
        expired_quote = expired_quote_res.json()
        with Session(engine) as db:
            before_stock = db.scalar(select(Inventory.stock_quantity).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            before_exchange_count = db.scalar(select(func.count(GarmentExchange.id)))
            before_quarantine_count = db.scalar(select(func.count(InventoryQuarantine.id)))
            before_payment_count = db.scalar(select(func.count(Payment.id)))
        expired_payload = {**stock_quote_request, "idempotency_key": "exchange-api-expired", "quote_fingerprint": expired_quote["quote_fingerprint"], "quote_expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}
        expired_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=expired_payload, headers=headers)
        assert expired_res.status_code == 409, expired_res.text
        assert expired_res.json()["detail"]["code"] == "EXCHANGE_QUOTE_EXPIRED"
        with Session(engine) as db:
            assert db.scalar(select(Inventory.stock_quantity).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id)) == before_stock
            assert db.scalar(select(func.count(GarmentExchange.id))) == before_exchange_count
            assert db.scalar(select(func.count(InventoryQuarantine.id))) == before_quarantine_count
            assert db.scalar(select(func.count(Payment.id))) == before_payment_count

        positive_payload = {"returned_variant_id": v1_id, "returned_quantity": 1, "new_variant_id": v3_id, "new_quantity": 1, "idempotency_key": "exchange-api-collection", "cash_tendered": 50}
        quote_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange/quote", json={k: positive_payload[k] for k in ("returned_variant_id", "returned_quantity", "new_variant_id", "new_quantity")}, headers=headers)
        assert quote_res.status_code == 200, quote_res.text
        positive_payload.update({"quote_fingerprint": quote_res.json()["quote_fingerprint"], "quote_expires_at": quote_res.json()["expires_at"]})
        res_collection = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=positive_payload, headers=headers)
        assert res_collection.status_code == 200, res_collection.text
        collection_data = res_collection.json()
        assert collection_data["difference"] == "30.00"
        assert Decimal(collection_data["cash_tendered"]) == Decimal("50.00")
        assert Decimal(collection_data["cash_change"]) == Decimal("20.00")
        assert collection_data["cash_refunded"] is None

        with Session(engine) as db:
            collection_payment = db.scalar(select(Payment).where(Payment.sale_id == confirmed_sale_id, Payment.provider == "EXCHANGE_REGISTER"))
            assert collection_payment is not None
            assert collection_payment.method == "CASH"
            assert collection_payment.status == "APPROVED"
            assert collection_payment.amount == Decimal("30.00")
            assert collection_payment.received_amount == Decimal("50.00")
            assert collection_payment.change_amount == Decimal("20.00")

        refund_payload = {"returned_variant_id": v1_id, "returned_quantity": 1, "new_variant_id": v4_id, "new_quantity": 1, "idempotency_key": "exchange-api-refund"}
        quote_res = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange/quote", json={k: refund_payload[k] for k in ("returned_variant_id", "returned_quantity", "new_variant_id", "new_quantity")}, headers=headers)
        assert quote_res.status_code == 200, quote_res.text
        refund_payload.update({"quote_fingerprint": quote_res.json()["quote_fingerprint"], "quote_expires_at": quote_res.json()["expires_at"]})
        res_unconfirmed_refund = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=refund_payload, headers=headers)
        assert res_unconfirmed_refund.status_code == 400
        assert res_unconfirmed_refund.json()["detail"]["code"] == "CASH_REFUND_CONFIRMATION_REQUIRED"
        refund_payload["cashier_confirmed"] = True
        res_refund = client.post(f"/api/v1/sales/{confirmed_sale_id}/exchange", json=refund_payload, headers=headers)
        assert res_refund.status_code == 200, res_refund.text
        refund_data = res_refund.json()
        assert refund_data["difference"] == "-50.00"
        assert refund_data["cash_refunded"] == "50.00"
        assert refund_data["cash_tendered"] is None
        assert refund_data["cash_change"] is None

        with Session(engine) as db:
            refund_exchange = db.scalar(select(GarmentExchange).where(GarmentExchange.idempotency_key == "exchange-api-refund"))
            assert refund_exchange.cash_refunded == Decimal("50.00")
            assert db.scalar(select(Payment).where(Payment.sale_id == confirmed_sale_id, Payment.provider == "EXCHANGE_REGISTER", Payment.amount == Decimal("50.00"))) is None
            foreign_tenant = Tenant(name="Foreign Tenant", status="ACTIVE")
            db.add(foreign_tenant)
            db.flush()
            inv2_db = db.scalar(select(Inventory).where(Inventory.product_variant_id == v2_id, Inventory.branch_id == b_id))
            inv2_db.tenant_id = foreign_tenant.id
            foreign_tenant_id = foreign_tenant.id
            db.commit()

        foreign_sale_res = client.post("/api/v1/sync/transactions", json={"operations": [{"client_operation_id": "op-api-foreign-inventory", "branch_id": b_id, "operation_type": "SALE", "sale_payload": {"items": [{"product_variant_id": v1_id, "quantity": 1, "unit_price": 150.0}], "total": 150.0}}]}, headers=headers)
        assert foreign_sale_res.status_code == 200
        foreign_sale_id = foreign_sale_res.json()["results"][0]["sale_id"]
        with Session(engine) as db:
            foreign_sale = db.scalar(select(Sale).where(Sale.id == foreign_sale_id))
            foreign_sale.tenant_id = foreign_tenant_id
            foreign_order_number = foreign_sale.order_number
            db.commit()
        foreign_lookup = client.get(f"/api/v1/sales/lookup/{foreign_order_number}", headers=headers)
        assert foreign_lookup.status_code == 404
        assert foreign_lookup.json()["detail"]["code"] == "SALE_NOT_FOUND"
        with Session(engine) as db:
            foreign_sale = db.scalar(select(Sale).where(Sale.id == foreign_sale_id))
            foreign_sale.tenant_id = tenant_id
            db.commit()

        foreign_exchange = {"returned_variant_id": v1_id, "returned_quantity": 1, "new_variant_id": v2_id, "new_quantity": 1, "idempotency_key": "exchange-api-foreign-inventory"}
        res_foreign_quote = client.post(f"/api/v1/sales/{foreign_sale_id}/exchange/quote", json={k: foreign_exchange[k] for k in ("returned_variant_id", "returned_quantity", "new_variant_id", "new_quantity")}, headers=headers)
        assert res_foreign_quote.status_code == 409
        assert res_foreign_quote.json()["detail"]["code"] == "NEW_ITEM_INVENTORY_NOT_FOUND"

    finally:
        if prev is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = prev


def test_cu22_offline_customer_minimal_data_in_sales_and_reservations():
    """CU-22: Verify minimal customer data (customer_name, customer_nit, customer_phone) is accepted and recorded in offline SALE and RESERVATION sync."""
    from decimal import Decimal
    from app.core.models import (
        Category,
        Color,
        Inventory,
        InventoryMovement,
        Product,
        ProductVariant,
        Reservation,
        Size,
    )
    from app.modules.sync.schemas import (
        OfflineReservationItemPayload,
        OfflineReservationPayload,
        OfflineSaleItemPayload,
        OfflineSalePayload,
        SyncTransactionBatchRequest,
        SyncTransactionItemRequest,
    )
    from app.modules.sync.service import process_sync_transactions_batch

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = Tenant(name="Boutique CU22", status="ACTIVE")
        city = City(name="Santa Cruz", is_active=True)
        session.add_all([tenant, city])
        session.flush()

        branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Sucursal Equipetrol", address="Av. San Martin", phone="3333333")
        role = Role(code="CASHIER", name="Cajero")
        session.add_all([branch, role])
        session.flush()

        cashier = User(
            tenant_id=tenant.id,
            role_id=role.id,
            first_name="Lucia",
            last_name="Rojas",
            email="lucia@cu22.local",
            phone="70000222",
            password_hash="secret",
            is_active=True,
        )
        session.add(cashier)
        session.flush()

        cat = Category(tenant_id=tenant.id, name="Vestidos", is_active=True)
        sz = Size(name="S", sort_order=1)
        col = Color(name="Rojo", hex_code="#FF0000")
        session.add_all([cat, sz, col])
        session.flush()

        prod = Product(tenant_id=tenant.id, category_id=cat.id, name="Vestido Gala", code="VES-01", slug="vestido-gala", price=Decimal("250.00"), is_active=True)
        session.add(prod)
        session.flush()

        variant = ProductVariant(tenant_id=tenant.id, product_id=prod.id, size_id=sz.id, color_id=col.id, sku="VES-01-S-ROJO", is_active=True)
        session.add(variant)
        session.flush()

        inv = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=variant.id, stock_quantity=10, reserved_quantity=0)
        session.add(inv)
        session.commit()

        batch = SyncTransactionBatchRequest(
            operations=[
                SyncTransactionItemRequest(
                    client_operation_id="op-cu22-sale-1",
                    branch_id=branch.id,
                    operation_type="SALE",
                    sale_payload=OfflineSalePayload(
                        customer_name="Roberto Carlos",
                        customer_nit="4589123015",
                        customer_phone="71234567",
                        items=[OfflineSaleItemPayload(product_variant_id=variant.id, quantity=1, unit_price=Decimal("250.00"))],
                        total=Decimal("250.00"),
                    ),
                ),
                SyncTransactionItemRequest(
                    client_operation_id="op-cu22-resv-1",
                    branch_id=branch.id,
                    operation_type="RESERVATION",
                    reservation_payload=OfflineReservationPayload(
                        customer_name="Elena Torrez",
                        customer_nit="8812345",
                        customer_phone="76543210",
                        items=[OfflineReservationItemPayload(product_variant_id=variant.id, quantity=1)],
                        notes="Pasa el viernes",
                    ),
                ),
            ]
        )

        res = process_sync_transactions_batch(session, cashier, batch)
        assert res.confirmed_count == 2

        sale_mov = session.query(InventoryMovement).filter_by(reference_id=res.results[0].sale_id).one()
        assert "Roberto Carlos" in sale_mov.reason
        assert "4589123015" in sale_mov.reason
        assert "71234567" in sale_mov.reason

        resv = session.query(Reservation).filter_by(id=res.results[1].reservation_id).one()
        assert "Elena Torrez" in resv.notes
        assert "8812345" in resv.notes
        assert "76543210" in resv.notes






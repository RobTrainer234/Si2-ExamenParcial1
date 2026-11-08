import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.models import (
    Base,
    Branch,
    Category,
    City,
    Color,
    Inventory,
    InventoryMovement,
    Permission,
    Product,
    ProductVariant,
    Role,
    RolePermission,
    Size,
    Tenant,
    User,
)
from app.core.security import hash_password
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)


def override_get_db():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
_previous_get_db_override = None


def setup_function() -> None:
    global _previous_get_db_override
    _previous_get_db_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with Session(engine) as db:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        client_role = Role(code="CLIENT", name="Cliente")
        db.add(client_role)
        db.commit()


def teardown_function() -> None:
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override



def test_ai_chat_virtual_fitting() -> None:
    res = client.post("/api/v1/ai/chat", json={"message": "¿Cómo funciona el vestidor virtual con realidad aumentada?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "Vestidor Virtual" in data["reply"] or "cámara" in data["reply"] or "realidad aumentada" in data["reply"].lower()
    assert data["provider"] in {"local", "openai"}


def test_ai_chat_promotions() -> None:
    res = client.post("/api/v1/ai/chat", json={"message": "¿Qué promociones o descuentos tienen hoy?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 10


def test_ai_chat_reservations() -> None:
    res = client.post("/api/v1/ai/chat", json={"message": "¿Cómo hago una reserva para probarme ropa en sucursal?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "reserv" in data["reply"].lower() or "sucursal" in data["reply"].lower()


def test_ai_chat_product_search() -> None:
    res = client.post("/api/v1/ai/chat", json={"message": "Busco camisa o vestido elegante"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert isinstance(data["suggested_products"], list)


def test_sale_return_restores_inventory() -> None:
    with Session(engine) as db:
        role = Role(code="CASHIER", name="Cajero")
        client_role = db.query(Role).filter_by(code="CLIENT").first()
        perm_sales_create = Permission(code="sales.create", name="Create sales")
        perm_sales_read = Permission(code="sales.read", name="Read sales")
        perm_payments_cash = Permission(code="payments.cash", name="Process cash payments")
        db.add_all([role, perm_sales_create, perm_sales_read, perm_payments_cash])
        db.flush()

        db.add_all([
            RolePermission(role_id=role.id, permission_id=perm_sales_create.id),
            RolePermission(role_id=role.id, permission_id=perm_sales_read.id),
            RolePermission(role_id=role.id, permission_id=perm_payments_cash.id),
        ])

        cat = Category(name="Return Cat")
        size = Size(name="Ret Size")
        color = Color(name="Ret Color", hex_code="#222222")
        city = City(name="Return City")
        tenant = Tenant(name="Return Tenant")
        db.add_all([cat, size, color, city, tenant])
        db.flush()

        branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Return Branch", address="Av Central 123", phone="71234567")
        prod = Product(tenant_id=tenant.id, category_id=cat.id, code="RET-PROD-1", name="Prenda Devolucion", slug="prenda-devolucion", price=150)
        db.add_all([branch, prod])
        db.flush()

        var = ProductVariant(tenant_id=tenant.id, product_id=prod.id, size_id=size.id, color_id=color.id, sku="RET-SKU-1")
        db.add(var)
        db.flush()

        inv = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=var.id, stock_quantity=10)
        db.add(inv)

        customer = User(tenant_id=tenant.id, role=client_role, first_name="Cliente", last_name="Retorno", email="customer.return@test.com", phone="70000000", password_hash=hash_password("Pass123!"))
        cashier = User(
            tenant_id=tenant.id,
            role=role,
            first_name="Cajero",
            last_name="Devoluciones",
            email="cashier.return@test.com",
            phone="78901234",
            password_hash=hash_password("Pass123!"),
        )
        cashier.branches.append(branch)
        db.add_all([customer, cashier])
        db.commit()

        branch_id = branch.id
        var_id = var.id
        inv_id = inv.id
        customer_id = customer.id

    # Iniciar sesión como cajero
    login_res = client.post("/api/v1/auth/login", json={"email": "cashier.return@test.com", "password": "Pass123!"})
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Crear venta presencial (3 unidades)
    sale_res = client.post("/api/v1/sales/physical", headers=headers, json={
        "branch_id": branch_id,
        "customer_id": customer_id,
        "items": [{"product_variant_id": var_id, "quantity": 3}],
    })
    assert sale_res.status_code == 201
    sale_id = sale_res.json()["id"]

    # Pagar la venta en caja -> status CONFIRMED y stock baja a 7
    pay_res = client.post(f"/api/v1/sales/{sale_id}/cash-payment", headers=headers, json={
        "method": "CASH",
        "amount": "450.00",
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "CONFIRMED"

    with Session(engine) as db:
        inv_after_sale = db.query(Inventory).filter_by(id=inv_id).first()
        assert inv_after_sale.stock_quantity == 7

    # Procesar devolución
    sale_item_id = sale_res.json()["items"][0]["id"]
    first_return = {
        "reason": "Cliente cambió de opinión sobre la prenda",
        "idempotency_key": "legacy-return-001",
        "items": [{"sale_item_id": sale_item_id, "quantity": 1, "condition": "SELLABLE"}],
    }
    return_res = client.post(f"/api/v1/sales/{sale_id}/return", headers=headers, json=first_return)
    assert return_res.status_code == 200
    assert return_res.json()["status"] == "CONFIRMED"
    assert return_res.json()["return_id"] > 0
    assert return_res.json()["credit_note_code"].startswith("NC-")
    assert return_res.json()["credit_note_amount"] == "150.00"

    second_return = client.post(f"/api/v1/sales/{sale_id}/return", headers=headers, json={
        "reason": "Cliente cambió de opinión sobre la prenda",
        "idempotency_key": "legacy-return-002",
        "items": [{"sale_item_id": sale_item_id, "quantity": 2, "condition": "SELLABLE"}],
    })
    assert second_return.status_code == 200
    assert second_return.json()["status"] == "RETURNED"

    replay = client.post(f"/api/v1/sales/{sale_id}/return", headers=headers, json=first_return)
    assert replay.status_code == 200
    conflict = client.post(f"/api/v1/sales/{sale_id}/return", headers=headers, json={**first_return, "reason": "Different request"})
    assert conflict.status_code == 409

    # Verificar que el stock se repuso a 10 and exactly one movement set exists per return.
    with Session(engine) as db:
        inv_after_return = db.query(Inventory).filter_by(id=inv_id).first()
        assert inv_after_return.stock_quantity == 10
        assert db.query(InventoryMovement).filter_by(movement_type="RETURN").count() == 2
        assert db.query(InventoryMovement).filter_by(movement_type="RESTOCK").count() == 2

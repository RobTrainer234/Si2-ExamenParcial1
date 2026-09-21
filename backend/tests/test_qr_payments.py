import os
from datetime import UTC, datetime
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.models import (
    Base,
    Branch,
    Cart,
    CartItem,
    Category,
    City,
    Color,
    Inventory,
    Payment,
    Product,
    ProductVariant,
    Role,
    Sale,
    SaleItem,
    SaleShippingSnapshot,
    Season,
    Size,
    User,
)
from app.core.security import hash_password
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)


def override_get_db():
    with Session(engine) as session:
        yield session


client = TestClient(app)
_previous_get_db_override = None


def setup_function() -> None:
    global _previous_get_db_override
    _previous_get_db_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with Session(engine) as db:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()

        user = User(
            role=admin_role,
            first_name="QR",
            last_name="Tester",
            email="qrtester@example.com",
            phone="71234599",
            password_hash=hash_password("Tester123!"),
        )
        db.add(user)
        db.commit()


def teardown_function() -> None:
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers() -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": "qrtester@example.com", "password": "Tester123!"})
    tokens = res.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_digital_sale_and_cart() -> tuple[int, int]:
    with Session(engine) as db:
        category = Category(name="Ropa QR")
        size = Size(name="L")
        color = Color(name="White", hex_code="#FFFFFF")
        season = Season(name="Invierno 26")
        city = City(name="La Paz")
        db.add_all([category, size, color, season, city])
        db.flush()

        branch = Branch(city_id=city.id, name="Sucursal Calacoto", address="Av. Ballivian 456", phone="71114455")
        product = Product(category_id=category.id, season_id=season.id, code="QR-01", name="Blusa Lino", slug="blusa-lino", price=Decimal("200.00"))
        db.add_all([branch, product])
        db.flush()

        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="QR-01-L-WHT")
        db.add(variant)
        db.flush()

        inv = Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=8, reserved_quantity=0)
        db.add(inv)
        db.flush()

        user = db.scalar(select(User).where(User.email == "qrtester@example.com"))
        cart = Cart(customer_id=user.id, status="ACTIVE")
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_variant_id=variant.id, quantity=1, unit_price=Decimal("200.00")))

        sale = Sale(
            order_number="ORD-QR-001",
            customer_id=user.id,
            branch_id=branch.id,
            channel="DIGITAL",
            fulfillment_type="DELIVERY",
            status="PENDING",
            subtotal=Decimal("200.00"),
            discount=Decimal("0.00"),
            total=Decimal("200.00"),
            created_at=datetime.now(UTC),
            shipping_snapshot=SaleShippingSnapshot(
                recipient_name="QR Tester",
                recipient_ci="9988776",
                recipient_phone="71234599",
                department_or_city="La Paz",
                zone="Calacoto",
                street="Av. Ballivian",
                house_number="456",
                reference="Ring the bell",
            ),
        )
        db.add(sale)
        db.flush()
        db.add(SaleItem(sale_id=sale.id, product_variant_id=variant.id, quantity=1, unit_price=Decimal("200.00"), discount=Decimal("0.00"), line_total=Decimal("200.00")))
        db.commit()
        return sale.id, inv.id


def test_generate_qr_payment() -> None:
    sale_id, _ = _seed_digital_sale_and_cart()
    headers = _headers()

    res = client.post("/api/v1/payments/qr/generate", json={"sale_id": sale_id}, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["sale_id"] == sale_id
    assert data["order_number"] == "ORD-QR-001"
    assert data["amount"] == "200.00"
    assert data["currency"] == "BOB"
    assert data["business_name"] == "FashionStore Atelier S.R.L."
    assert data["bank_name"] == "Banco Nacional de Bolivia (BNB)"
    assert data["transaction_reference"].startswith("QR-FASHION-")
    assert "https://api.qrserver.com" in data["qr_image_url"]


def test_simulate_qr_payment_success_deducts_stock_and_clears_cart() -> None:
    sale_id, inv_id = _seed_digital_sale_and_cart()
    headers = _headers()

    qr_res = client.post("/api/v1/payments/qr/generate", json={"sale_id": sale_id}, headers=headers)
    assert qr_res.status_code == 201
    ref = qr_res.json()["transaction_reference"]

    # Simular transferencia exitosa con monto exacto
    sim_res = client.post(
        "/api/v1/payments/qr/simulate",
        json={"transaction_reference": ref, "amount": 200.00},
        headers=headers,
    )
    assert sim_res.status_code == 200
    sale_data = sim_res.json()
    assert sale_data["status"] == "CONFIRMED"
    assert sale_data["fulfillment_type"] == "DELIVERY"
    assert sale_data["shipping_details"]["recipient_name"] == "QR Tester"

    with Session(engine) as db:
        # Pago aprobado
        sale = db.scalar(select(Sale).where(Sale.id == sale_id))
        assert sale.shipping_snapshot is not None
        assert sale.shipping_snapshot.recipient_name == "QR Tester"

        payment = db.scalar(select(Payment).where(Payment.transaction_reference == ref))
        assert payment.status == "APPROVED"
        assert payment.received_amount == Decimal("200.00")

        # Stock descontado (era 8, ahora debe ser 7)
        inv = db.scalar(select(Inventory).where(Inventory.id == inv_id))
        assert inv.stock_quantity == 7

        # Carrito vaciado
        user = db.scalar(select(User).where(User.email == "qrtester@example.com"))
        cart = db.scalar(select(Cart).where(Cart.customer_id == user.id))
        assert len(cart.items) == 0


def test_simulate_qr_payment_mismatched_amount_rejected() -> None:
    sale_id, _ = _seed_digital_sale_and_cart()
    headers = _headers()

    qr_res = client.post("/api/v1/payments/qr/generate", json={"sale_id": sale_id}, headers=headers)
    ref = qr_res.json()["transaction_reference"]

    # Simular transferencia con monto menor (mismatch)
    sim_res = client.post(
        "/api/v1/payments/qr/simulate",
        json={"transaction_reference": ref, "amount": 50.00},
        headers=headers,
    )
    assert sim_res.status_code == 409


def test_qr_status_polling_and_confirm_transfer() -> None:
    sale_id, inv_id = _seed_digital_sale_and_cart()
    headers = _headers()

    qr_res = client.post(
        "/api/v1/payments/qr/generate",
        json={"sale_id": sale_id, "client_base_url": "http://192.168.0.7:4200"},
        headers=headers,
    )
    assert qr_res.status_code == 201
    ref = qr_res.json()["transaction_reference"]
    assert "banca-movil?ref=" in qr_res.json()["qr_data"]

    # Consultar estado pendiente inicial
    status_res = client.get(f"/api/v1/payments/qr/status/{ref}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "PENDING"
    assert status_res.json()["is_confirmed"] is False

    # Confirmar desde la pantalla de banca móvil
    confirm_res = client.post(
        "/api/v1/payments/qr/confirm-transfer",
        json={"transaction_reference": ref, "amount": 200.00},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"
    assert confirm_res.json()["shipping_details"]["recipient_name"] == "QR Tester"

    # Polling ahora debe devolver APPROVED y is_confirmed True
    status_after = client.get(f"/api/v1/payments/qr/status/{ref}")
    assert status_after.status_code == 200
    assert status_after.json()["status"] == "APPROVED"
    assert status_after.json()["is_confirmed"] is True

    # Verificar stock
    with Session(engine) as db:
        inv = db.scalar(select(Inventory).where(Inventory.id == inv_id))
        assert inv.stock_quantity == 7

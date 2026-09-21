import os
from datetime import UTC, datetime
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock_for_unit_tests"
os.environ["STRIPE_CURRENCY"] = "bob"

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
            first_name="Stripe",
            last_name="Shopper",
            email="shopper@example.com",
            phone="71234567",
            password_hash=hash_password("Shopper123!"),
        )
        db.add(user)
        db.commit()


def teardown_function() -> None:
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers() -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": "shopper@example.com", "password": "Shopper123!"})
    if res.status_code != 200:
        raise RuntimeError(f"Login failed: {res.status_code} {res.text}")
    tokens = res.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_digital_sale_and_cart() -> tuple[int, int]:
    with Session(engine) as db:
        category = Category(name="Stripe Cat")
        size = Size(name="M")
        color = Color(name="Black", hex_code="#000000")
        season = Season(name="Summer 26")
        city = City(name="Santa Cruz")
        db.add_all([category, size, color, season, city])
        db.flush()

        branch = Branch(city_id=city.id, name="Sucursal Equipetrol", address="Av. San Martin 123", phone="71112233")
        product = Product(category_id=category.id, season_id=season.id, code="STRP-01", name="Vestido Seda", slug="vestido-seda", price=Decimal("150.00"))
        db.add_all([branch, product])
        db.flush()

        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="STRP-01-M-BLK")
        db.add(variant)
        db.flush()

        inv = Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=10, reserved_quantity=0)
        db.add(inv)
        db.flush()

        user = db.scalar(select(User).where(User.email == "shopper@example.com"))
        cart = Cart(customer_id=user.id, status="ACTIVE")
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_variant_id=variant.id, quantity=1, unit_price=Decimal("150.00")))

        sale = Sale(
            order_number="ORD-STRIPE-001",
            customer_id=user.id,
            branch_id=branch.id,
            channel="DIGITAL",
            fulfillment_type="DELIVERY",
            status="PENDING",
            subtotal=Decimal("150.00"),
            discount=Decimal("0.00"),
            total=Decimal("150.00"),
            created_at=datetime.now(UTC),
            shipping_snapshot=SaleShippingSnapshot(
                recipient_name="Stripe Shopper",
                recipient_ci="7654321",
                recipient_phone="71234567",
                department_or_city="Santa Cruz",
                zone="Equipetrol",
                street="Av. San Martin",
                house_number="123",
                reference="Leave at reception",
            ),
        )
        db.add(sale)
        db.flush()
        db.add(SaleItem(sale_id=sale.id, product_variant_id=variant.id, quantity=1, unit_price=Decimal("150.00"), discount=Decimal("0.00"), line_total=Decimal("150.00")))
        db.commit()
        return sale.id, inv.id


def test_create_stripe_payment_intent_and_idempotency() -> None:
    sale_id, _ = _seed_digital_sale_and_cart()
    headers = _headers()

    payload = {
        "sale_id": sale_id,
        "idempotency_key": "stripe-key-test-001",
        "method": "CARD",
    }
    response = client.post("/api/v1/payments/stripe/intent", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["sale_id"] == sale_id
    assert data["provider"] == "STRIPE"
    assert data["payment_intent_id"].startswith("pi_")
    assert "client_secret" in data
    assert data["amount"] == "150.00"
    assert data["status"] == "PENDING"
    assert data["currency"] == "BOB"

    # Idempotencia: misma clave retorna el mismo intent
    response_repeat = client.post("/api/v1/payments/stripe/intent", json=payload, headers=headers)
    assert response_repeat.status_code == 201
    assert response_repeat.json()["payment_intent_id"] == data["payment_intent_id"]
    assert response_repeat.json()["client_secret"] == data["client_secret"]


def test_confirm_stripe_payment_deducts_inventory_and_clears_cart() -> None:
    from unittest.mock import MagicMock, patch

    sale_id, inv_id = _seed_digital_sale_and_cart()
    headers = _headers()

    intent_res = client.post(
        "/api/v1/payments/stripe/intent",
        json={"sale_id": sale_id, "idempotency_key": "stripe-key-test-002", "method": "CARD"},
        headers=headers,
    )
    assert intent_res.status_code == 201
    intent_id = intent_res.json()["payment_intent_id"]

    # Confirmar pago con mock de verificación de Stripe succeeded
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": intent_id, "status": "succeeded"}

    with patch("httpx.get", return_value=mock_resp):
        confirm_res = client.post(
            "/api/v1/payments/stripe/confirm",
            json={"payment_intent_id": intent_id},
            headers=headers,
        )
    assert confirm_res.status_code == 200
    sale_data = confirm_res.json()
    assert sale_data["status"] == "CONFIRMED"
    assert sale_data["fulfillment_type"] == "DELIVERY"
    assert sale_data["shipping_details"]["recipient_name"] == "Stripe Shopper"

    with Session(engine) as db:
        # Verificar estado del pago
        sale = db.scalar(select(Sale).where(Sale.id == sale_id))
        assert sale.shipping_snapshot is not None
        assert sale.shipping_snapshot.recipient_name == "Stripe Shopper"

        payment = db.scalar(select(Payment).where(Payment.transaction_reference == intent_id))
        assert payment.status == "APPROVED"
        assert payment.paid_at is not None

        # Verificar inventario descontado (era 10, ahora debe ser 9)
        inv = db.scalar(select(Inventory).where(Inventory.id == inv_id))
        assert inv.stock_quantity == 9

        # Verificar carrito vaciado
        user = db.scalar(select(User).where(User.email == "shopper@example.com"))
        cart = db.scalar(select(Cart).where(Cart.customer_id == user.id))
        assert len(cart.items) == 0


def test_create_stripe_intent_rejects_already_confirmed_or_nonexistent_sale() -> None:
    from unittest.mock import MagicMock, patch

    sale_id, _ = _seed_digital_sale_and_cart()
    headers = _headers()

    # Venta inexistente
    res_404 = client.post(
        "/api/v1/payments/stripe/intent",
        json={"sale_id": 999999, "idempotency_key": "key-404", "method": "CARD"},
        headers=headers,
    )
    assert res_404.status_code == 404

    # Confirmar venta primero
    intent = client.post(
        "/api/v1/payments/stripe/intent",
        json={"sale_id": sale_id, "idempotency_key": "key-to-confirm", "method": "CARD"},
        headers=headers,
    ).json()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": intent["payment_intent_id"], "status": "succeeded"}

    with patch("httpx.get", return_value=mock_resp):
        client.post("/api/v1/payments/stripe/confirm", json={"payment_intent_id": intent["payment_intent_id"]}, headers=headers)

    # Tratar de crear otro intent para la venta ya confirmada
    res_conflict = client.post(
        "/api/v1/payments/stripe/intent",
        json={"sale_id": sale_id, "idempotency_key": "new-key-for-confirmed", "method": "CARD"},
        headers=headers,
    )
    assert res_conflict.status_code == 409


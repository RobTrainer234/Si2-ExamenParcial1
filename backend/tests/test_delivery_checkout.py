import os
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
    Permission,
    Product,
    ProductVariant,
    Role,
    Sale,
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
        permissions = [Permission(code=code, name=code) for code in ["cart.manage", "payments.electronic", "sales.read"]]
        client_role = Role(code="CLIENT", name="Cliente", permissions=permissions)
        other_role = Role(code="CLIENT_OTHER", name="Otro cliente", permissions=permissions)
        db.add_all([client_role, other_role])
        db.flush()
        db.add_all(
            [
                User(
                    role=client_role,
                    first_name="Delivery",
                    last_name="Buyer",
                    email="buyer@example.com",
                    phone="70000010",
                    password_hash=hash_password("Buyer123!"),
                ),
                User(
                    role=other_role,
                    first_name="Other",
                    last_name="Buyer",
                    email="other@example.com",
                    phone="70000011",
                    password_hash=hash_password("Other123!"),
                ),
            ]
        )
        db.commit()


def teardown_function() -> None:
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers(email: str = "buyer@example.com", password: str = "Buyer123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _seed_cart(email: str = "buyer@example.com") -> tuple[int, int]:
    with Session(engine) as db:
        category = Category(name=f"Delivery Cat {email}")
        size = Size(name=f"M {email}")
        color = Color(name=f"Blue {email}", hex_code="#0000FF")
        season = Season(name=f"Season {email}")
        city = City(name=f"City {email}")
        db.add_all([category, size, color, season, city])
        db.flush()
        branch = Branch(city_id=city.id, name=f"Branch {email}", address="Main 123", phone="70000000")
        product = Product(category_id=category.id, season_id=season.id, code=f"DEL-{email[:3]}", name="Delivery Shirt", slug=f"delivery-shirt-{email[:3]}", price=Decimal("120.00"))
        db.add_all([branch, product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku=f"DEL-{email[:3]}-M-BLU")
        db.add(variant)
        db.flush()
        db.add(Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=5, reserved_quantity=0))
        user = db.scalar(select(User).where(User.email == email))
        cart = Cart(customer_id=user.id, status="ACTIVE")
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_variant_id=variant.id, quantity=1, unit_price=Decimal("120.00")))
        db.commit()
        return branch.id, variant.id


def _shipping_details() -> dict[str, str]:
    return {
        "recipient_name": "Ana Lopez",
        "recipient_ci": "1234567",
        "recipient_phone": "70000022",
        "department_or_city": "Santa Cruz",
        "zone": "Equipetrol",
        "street": "Av. San Martin",
        "house_number": "123",
        "reference": "Casa blanca frente al parque",
    }


def test_digital_purchase_with_only_branch_id_defaults_to_pickup() -> None:
    branch_id, _ = _seed_cart()
    response = client.post("/api/v1/purchases/digital", json={"branch_id": branch_id}, headers=_headers())

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["fulfillment_type"] == "PICKUP"
    assert data["shipping_details"] is None
    assert data["total"] == "120.00"

    with Session(engine) as db:
        sale = db.scalar(select(Sale).where(Sale.id == data["id"]))
        assert sale.fulfillment_type == "PICKUP"
        assert sale.shipping_snapshot is None


def test_delivery_requires_complete_well_formed_shipping_details() -> None:
    branch_id, _ = _seed_cart()
    headers = _headers()

    missing = client.post("/api/v1/purchases/digital", json={"branch_id": branch_id, "fulfillment_type": "DELIVERY"}, headers=headers)
    assert missing.status_code == 422
    assert missing.json()["detail"]

    malformed = client.post(
        "/api/v1/purchases/digital",
        json={"branch_id": branch_id, "fulfillment_type": "DELIVERY", "shipping_details": {**_shipping_details(), "street": "   "}},
        headers=headers,
    )
    assert malformed.status_code == 422
    assert malformed.json()["detail"]


def test_invalid_fulfillment_type_is_rejected_with_structured_error() -> None:
    branch_id, _ = _seed_cart()
    response = client.post("/api/v1/purchases/digital", json={"branch_id": branch_id, "fulfillment_type": "DRONE"}, headers=_headers())

    assert response.status_code == 422
    assert response.json()["detail"]


def test_delivery_purchase_serializes_shipping_snapshot_and_keeps_totals_unchanged() -> None:
    branch_id, _ = _seed_cart()
    response = client.post(
        "/api/v1/purchases/digital",
        json={"branch_id": branch_id, "fulfillment_type": "DELIVERY", "shipping_details": _shipping_details()},
        headers=_headers(),
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["fulfillment_type"] == "DELIVERY"
    assert data["shipping_details"] == _shipping_details()
    assert data["subtotal"] == "120.00"
    assert data["total"] == "120.00"

    history = client.get("/api/v1/purchases/mine", headers=_headers())
    assert history.status_code == 200
    assert history.json()["items"][0]["shipping_details"] == _shipping_details()

    with Session(engine) as db:
        snapshot = db.scalar(select(SaleShippingSnapshot).where(SaleShippingSnapshot.sale_id == data["id"]))
        assert snapshot is not None
        assert snapshot.recipient_name == "Ana Lopez"


def test_other_customer_cannot_read_delivery_shipping_snapshot() -> None:
    branch_id, _ = _seed_cart()
    sale = client.post(
        "/api/v1/purchases/digital",
        json={"branch_id": branch_id, "fulfillment_type": "DELIVERY", "shipping_details": _shipping_details()},
        headers=_headers(),
    ).json()

    response = client.get("/api/v1/purchases/mine", headers=_headers("other@example.com", "Other123!"))
    assert response.status_code == 200
    assert response.json()["items"] == []

    forbidden = client.get(f"/api/v1/purchases/mine/{sale['id']}", headers=_headers("other@example.com", "Other123!"))
    assert forbidden.status_code == 404

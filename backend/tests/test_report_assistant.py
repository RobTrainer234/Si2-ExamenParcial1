import os
from datetime import UTC, datetime
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, Branch, Category, City, Color, Inventory, Permission, Product, ProductVariant, Role, RolePermission, Sale, SaleItem, Season, Size, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.reports import ai_service  # noqa: E402

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
        seller_role = Role(code="SELLER", name="Vendedor")
        reports_role = Role(code="REPORTS", name="Reportes")
        reports_permission = Permission(code="reports.read", name="Consultar reportes")
        db.add_all([admin_role, seller_role, reports_role, reports_permission])
        db.flush()
        db.add(RolePermission(role_id=reports_role.id, permission_id=reports_permission.id))
        db.add_all(
            [
                User(role=admin_role, first_name="Admin", last_name="Reports", email="admin-reports@example.com", phone="70000090", password_hash=hash_password("Admin123!")),
                User(role=seller_role, first_name="Seller", last_name="Reports", email="seller-reports@example.com", phone="70000091", password_hash=hash_password("Seller123!")),
                User(role=reports_role, first_name="Reader", last_name="Reports", email="reader-reports@example.com", phone="70000092", password_hash=hash_password("Reader123!")),
            ]
        )
        db.commit()


def teardown_function() -> None:
    ai_service.settings.openai_api_key = None
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers(email: str = "admin-reports@example.com", password: str = "Admin123!") -> dict[str, str]:
    tokens = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_report_data() -> None:
    with Session(engine) as db:
        category = Category(name="Assistant Category")
        size = Size(name="Assistant M")
        color = Color(name="Assistant Blue", hex_code="#0000FF")
        season = Season(name="Assistant Season")
        city = City(name="La Paz")
        db.add_all([category, size, color, season, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Sucursal Central", address="Av. Principal 123", phone="70000000")
        shirt = Product(category_id=category.id, season_id=season.id, code="AST-001", name="Camisa Urbana", slug="camisa-urbana", price=Decimal("150.00"))
        jacket = Product(category_id=category.id, season_id=season.id, code="AST-002", name="Chaqueta Denim", slug="chaqueta-denim", price=Decimal("300.00"))
        db.add_all([branch, shirt, jacket])
        db.flush()
        shirt_variant = ProductVariant(product_id=shirt.id, size_id=size.id, color_id=color.id, sku="AST-001-M-BLUE")
        jacket_variant = ProductVariant(product_id=jacket.id, size_id=size.id, color_id=color.id, sku="AST-002-M-BLUE")
        db.add_all([shirt_variant, jacket_variant])
        db.flush()
        db.add_all(
            [
                Inventory(branch_id=branch.id, product_variant_id=shirt_variant.id, stock_quantity=5, reserved_quantity=1),
                Inventory(branch_id=branch.id, product_variant_id=jacket_variant.id, stock_quantity=20, reserved_quantity=0),
            ]
        )
        sale = Sale(
            order_number="AST-0001",
            branch_id=branch.id,
            channel="PHYSICAL",
            status="CONFIRMED",
            subtotal=Decimal("900.00"),
            discount=Decimal("0.00"),
            total=Decimal("900.00"),
            created_at=datetime(2024, 5, 20, 12, 0, tzinfo=UTC),
        )
        db.add(sale)
        db.flush()
        db.add_all(
            [
                SaleItem(sale_id=sale.id, product_variant_id=shirt_variant.id, quantity=4, unit_price=Decimal("150.00"), discount=Decimal("0.00"), line_total=Decimal("600.00")),
                SaleItem(sale_id=sale.id, product_variant_id=jacket_variant.id, quantity=1, unit_price=Decimal("300.00"), discount=Decimal("0.00"), line_total=Decimal("300.00")),
            ]
        )
        db.commit()


def test_assistant_local_top_products_uses_grounded_report_data() -> None:
    ai_service.settings.openai_api_key = None
    _seed_report_data()

    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": "Mostrame los productos más vendidos de mayo"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["fallback_used"] is True
    assert body["intent"]["kind"] == "top_products"
    assert body["data"][0]["product_name"] == "Camisa Urbana"
    assert body["data"][0]["units_sold"] == 4
    assert "Camisa Urbana" in body["narrative"]


def test_assistant_falls_back_when_openai_response_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    ai_service.settings.openai_api_key = "test-key"
    _seed_report_data()

    def invalid_provider(_: dict[str, object]) -> dict[str, object]:
        return {"output_text": "no es json"}

    monkeypatch.setattr(ai_service, "_post_openai", invalid_provider)

    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": "Necesito revisar el inventario bajo"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["fallback_used"] is True
    assert body["intent"]["kind"] == "inventory"
    assert body["data"][0]["product_name"] == "Camisa Urbana"


def test_assistant_requires_reports_read_permission() -> None:
    unauthenticated = client.post("/api/v1/reports/assistant", json={"prompt": "Resumen del dashboard"})
    forbidden = client.post("/api/v1/reports/assistant", headers=_headers("seller-reports@example.com", "Seller123!"), json={"prompt": "Resumen del dashboard"})

    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403


def test_assistant_uses_mocked_openai_intent_without_trusting_model_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    ai_service.settings.openai_api_key = "test-key"
    _seed_report_data()
    calls = {"count": 0}

    def mocked_provider(_: dict[str, object]) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {"output_text": '{"kind":"sales_by_branch","filters":{"date_from":null,"date_to":null,"branch_id":null},"reasoning":"Pedido por sucursal."}'}
        return {"output_text": "La sucursal central concentra las ventas confirmadas según los datos suministrados."}

    monkeypatch.setattr(ai_service, "_post_openai", mocked_provider)

    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": "Dame ventas por sucursal"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai"
    assert body["fallback_used"] is False
    assert body["intent"]["kind"] == "sales_by_branch"
    assert body["data"][0]["branch_name"] == "Sucursal Central"
    assert body["data"][0]["total"] == "900.00"
    assert calls["count"] == 2


def test_assistant_inventory_urgent_replenishment_intent() -> None:
    ai_service.settings.openai_api_key = None
    _seed_report_data()

    query = "¿Cuáles productos tienen bajo stock y requieren reposición urgente?"
    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": query})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["kind"] == "inventory"
    assert body["provider"] == "local"
    assert len(body["data"]) >= 1
    assert body["data"][0]["product_name"] == "Camisa Urbana"
    assert body["data"][0]["available_quantity"] == 4
    assert "bajo stock" in body["narrative"].lower()
    assert "Camisa Urbana" in body["narrative"]

